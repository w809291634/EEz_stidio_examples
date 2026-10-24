/*
 * 真机平台实现入口。
 * 设备工程必须定义 WATCH_PLATFORM_DEVICE，并在本文件接入 RTC、BLE、传感器、PWM、NVS。
 * 不提供“看似能工作”的空桩，避免真机误链接到 PC 行为。
 */
#if defined(WATCH_PLATFORM_DEVICE)
#error "Implement platform/device/watch_platform_device.c for the selected board before enabling WATCH_PLATFORM_DEVICE"
#endif
