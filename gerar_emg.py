import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal as sg

# ===== PARÂMETROS =====
fs = 1000          # Hz (1 kHz)
duration = 3.0     # segundos
n_samples = int(fs * duration)
t = np.linspace(0, duration, n_samples, endpoint=False)

# ===== 1. GERAR SINAL EMG SINTÉTICO =====
np.random.seed(42)

# Ruído branco gaussiano
noise = np.random.randn(n_samples)

# Filtro passa-banda 20-450 Hz (Butterworth 4ª ordem)
sos = sg.butter(4, [20/500, 450/500], btype='band', output='sos')
emg = sg.sosfiltfilt(sos, noise)

# ===== 2. ENVELOPE DE CONTRAÇÃO =====
envelope = np.zeros(n_samples)
n_rest_1 = int(0.5 * fs)
n_ramp_up = int(0.6 * fs)
n_hold = int(0.8 * fs)
n_ramp_down = int(0.6 * fs)
n_rest_2 = int(0.5 * fs)

n_total = n_rest_1 + n_ramp_up + n_hold + n_ramp_down + n_rest_2
diff = n_samples - n_total
n_hold += diff

rest = np.zeros(n_rest_1)
ramp_up = np.linspace(0, 1, n_ramp_up)**1.5
hold = np.ones(n_hold)
ramp_down = np.linspace(1, 0, n_ramp_down)**2
rest2 = np.zeros(n_rest_2)

envelope = np.concatenate([rest, ramp_up, hold, ramp_down, rest2])

# Amplitude de pico (±1.5 mV)
amp_peak = 0.0015  # Volts
emg_scaled = emg * envelope * amp_peak / np.std(emg)

print(f"Amplitude pico-a-pico: {np.ptp(emg_scaled)*1e6:.0f} \u00b5V")
print(f"RMS (contra\u00e7\u00e3o): {np.std(emg_scaled[envelope > 0.5])*1e6:.0f} \u00b5V")

# ===== 3. PLOT =====
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7),
                                gridspec_kw={'height_ratios': [3, 1]})

ax1.plot(t, emg_scaled * 1e6, linewidth=0.6, color='#2ecc71')
ax1.set_ylabel('Amplitude (\u00b5V)', fontsize=12)
ax1.set_title(
    f'Sinal EMG Sint\u00e9tico \u2014 20-450 Hz, {fs} Hz, {duration} s',
    fontsize=13, fontweight='bold')
ax1.set_xlim(0, duration)
ax1.grid(True, alpha=0.3)

ax2.fill_between(t, envelope * 100, alpha=0.3, color='#3498db')
ax2.plot(t, envelope * 100, linewidth=1, color='#3498db')
ax2.set_ylabel('For\u00e7a (%)', fontsize=12)
ax2.set_xlabel('Tempo (s)', fontsize=12)
ax2.set_xlim(0, duration)
ax2.set_ylim(0, 110)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('/home/hermes/emg_sintetico.png', dpi=150)
print("\nGr\u00e1fico salvo!")

# ===== 4. GERAR HEADER C PRA DAC =====

# --- Opção 1: int16 (bipolar) - DAC externo ---
# Range: ±1V na saída do DAC (ajustar atenuador externo)
v_ref_int16 = 1.0  # ±1V
emg_int16 = np.clip(emg_scaled / v_ref_int16 * 32767,
                     -32768, 32767).astype(np.int16)

# --- Opção 2: uint12 (unipolar) - DAC interno STM32/ESP32 ---
# EMG está em mV. Para usar bem os 12 bits do DAC (0-3.3V),
# amplificamos o sinal antes de somar o offset. O atenuador
# externo reduz de volta para o nível fisiológico.
dac_ref = 3.3       # Volts
dac_bits = 12
dac_max = (1 << dac_bits) - 1
ganho_dac = 200     # amplifica mV -> V no DAC
v_offset = dac_ref / 2

emg_amplified = emg_scaled * ganho_dac
emg_centered = emg_amplified + v_offset
emg_uint12 = np.clip(emg_centered / dac_ref * dac_max, 0, dac_max).astype(np.uint16)

# Salvar header int16
with open('/home/hermes/emg_signal_int16.h', 'w') as f:
    f.write(f'// Sinal EMG sint\u00e9tico\n')
    f.write(f'// Taxa: {fs} Hz\n')
    f.write(f'// Dura\u00e7\u00e3o: {duration} s\n')
    f.write(f'// Amostras: {len(emg_int16)}\n')
    f.write(f'// Sa\u00edda DAC: \u00b1{v_ref_int16} V (ajustar atenuador externo)\n')
    f.write(f'// Banda: 20-450 Hz\n')
    f.write(f'// Formato: int16 (little-endian)\n\n')
    f.write(f'#define EMG_FS {fs}\n')
    f.write(f'#define EMG_N_SAMPLES {len(emg_int16)}\n')
    f.write(f'#define EMG_VREF {v_ref_int16}f\n\n')
    f.write(f'const int16_t emg_signal[{len(emg_int16)}] = {{\n')
    for i, val in enumerate(emg_int16):
        if i % 8 == 0:
            f.write('    ')
        f.write(f'{val:6d}, ')
        if i % 8 == 7:
            f.write('\n')
    if len(emg_int16) % 8 != 0:
        f.write('\n')
    f.write('};\n')

# Salvar header uint12
with open('/home/hermes/emg_signal_uint12.h', 'w') as f:
    f.write(f'// Sinal EMG sint\u00e9tico - formato uint12\n')
    f.write(f'// DAC interno MCU (0-{dac_ref}V, {dac_bits} bits)\n')
    f.write(f'// Taxa: {fs} Hz\n')
    f.write(f'// Dura\u00e7\u00e3o: {duration} s\n')
    f.write(f'// Amostras: {len(emg_uint12)}\n')
    f.write(f'// Ganho interno: {ganho_dac}x (atenuador externo ajusta)\n')
    f.write(f'// Banda: 20-450 Hz\n\n')
    f.write(f'#define EMG_FS {fs}\n')
    f.write(f'#define EMG_N_SAMPLES {len(emg_uint12)}\n')
    f.write(f'#define EMG_DAC_MAX {dac_max}\n\n')
    f.write(f'const uint16_t emg_signal[{len(emg_uint12)}] = {{\n')
    for i, val in enumerate(emg_uint12):
        if i % 8 == 0:
            f.write('    ')
        f.write(f'{val:5d}, ')
        if i % 8 == 7:
            f.write('\n')
    if len(emg_uint12) % 8 != 0:
        f.write('\n')
    f.write('};\n')

# Salvar raw binário
emg_int16.tofile('/home/hermes/emg_signal_int16.raw')

print(f"\nHeader C int16: /home/hermes/emg_signal_int16.h ({len(emg_int16)} amostras)")
print(f"Header C uint12: /home/hermes/emg_signal_uint12.h ({len(emg_uint12)} amostras)")
print(f"Raw bin\u00e1rio: /home/hermes/emg_signal_int16.raw ({len(emg_int16)*2} bytes)")
print(f"\n--- Info do sinal ---")
print(f"RMS da contra\u00e7\u00e3o: {np.std(emg_scaled[envelope > 0.5])*1e6:.0f} \u00b5V")
print(f"Pico: {emg_scaled.max()*1e6:.0f} \u00b5V")
print(f"Vale: {emg_scaled.min()*1e6:.0f} \u00b5V")
