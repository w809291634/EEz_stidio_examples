#!/usr/bin/env python3
# Extract unicode codepoints present in a TTF's 'cmap' table (pure stdlib).
import sys, struct

def extract(path):
    with open(path, "rb") as f:
        data = f.read()
    # Read sfnt version + num tables
    if data[:4] not in (b"\x00\x01\x00\x00", b"true", b"OTTO"):
        # woff? just bail
        pass
    num = struct.unpack(">H", data[4:6])[0]
    tables = {}
    off = 12
    for i in range(num):
        tag = data[off:off+4].decode("latin1")
        # checksum 4, offset 4, length 4
        toff = struct.unpack(">I", data[off+8:off+12])[0]
        tlen = struct.unpack(">I", data[off+12:off+16])[0]
        tables[tag] = (toff, tlen)
        off += 16
    if "cmap" not in tables:
        return []
    coff, clen = tables["cmap"]
    # cmap header: version(2), numTables(2)
    nsub = struct.unpack(">H", data[coff+2:coff+4])[0]
    records = []
    p = coff + 4
    for i in range(nsub):
        pid = struct.unpack(">H", data[p:p+2])[0]
        eid = struct.unpack(">H", data[p+2:p+4])[0]
        suboff = struct.unpack(">I", data[p+4:p+8])[0]
        records.append((pid, eid, coff + suboff))
        p += 8
    codepoints = set()
    for pid, eid, suboff in records:
        fmt = struct.unpack(">H", data[suboff:suboff+2])[0]
        if fmt == 4:
            # format 4
            segX2 = struct.unpack(">H", data[suboff+6:suboff+8])[0]
            segc = segX2 // 2
            base = suboff + 14
            endChars = struct.unpack(">%dH" % segc, data[base:base+segX2])
            base2 = base + segX2 + 2
            startChars = struct.unpack(">%dH" % segc, data[base2:base2+segX2])
            base3 = base2 + segX2
            idDelta = struct.unpack(">%dh" % segc, data[base3:base3+segX2])
            base4 = base3 + segX2
            idRangeOff = struct.unpack(">%dH" % segc, data[base4:base4+segX2])
            for i in range(segc):
                sc = startChars[i]
                ec = endChars[i]
                if sc == 0xFFFF:
                    continue
                for cp in range(sc, ec+1):
                    d = idDelta[i]
                    ro = idRangeOff[i]
                    if ro == 0:
                        gi = (cp + d) & 0xFFFF
                    else:
                        addr = base4 + i*2 + ro + (cp - sc)*2
                        gi = struct.unpack(">H", data[addr:addr+2])[0]
                        if gi == 0:
                            continue
                    codepoints.add(cp)
        elif fmt == 12:
            n = struct.unpack(">I", data[suboff+12:suboff+16])[0]
            p2 = suboff + 16
            for i in range(n):
                sc = struct.unpack(">I", data[p2:p2+4])[0]
                ec = struct.unpack(">I", data[p2+4:p2+8])[0]
                p2 += 12
                for cp in range(sc, ec+1):
                    codepoints.add(cp)
    return sorted(codepoints)

if __name__ == "__main__":
    cps = extract(sys.argv[1])
    print("COUNT=%d" % len(cps))
    s = "".join(chr(c) for c in cps)
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write(s)
    print("WROTE=%s" % sys.argv[2])
