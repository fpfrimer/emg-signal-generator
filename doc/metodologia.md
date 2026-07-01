# Metodologia de Geração de Sinal EMG Sintético

## 1. Fundamentos Fisiológicos do EMG

O eletromiograma de superfície (sEMG) é o registro da atividade elétrica gerada pelas
unidades motoras durante a contração muscular. Quando um potencial de ação percorre
o axônio motor até a junção neuromuscular, desencadeia a despolarização de todas as
fibras musculares inervadas por aquela unidade motora — este evento é chamado de
**Potencial de Ação de Unidade Motora (MUAP)**.

O sinal captado na superfície da pele é a **sobreposição espacial e temporal** de
centenas de MUAPs de diferentes unidades motoras. Pelo Teorema Central do Limite,
quando muitas unidades motoras são recrutadas (contrações moderadas a fortes), a
distribuição de amplitude do sinal EMG se aproxima de uma **Gaussiana** com média zero
[Nawab et al., 2010; Farina & Merletti, 2004].

## 2. Modelo do Sinal

O gerador utiliza um modelo estocástico de **ruído Gaussiano branco filtrado**:

```
x(t) = BPF{ w(t) } · e(t) · A
```

Onde:

| Termo | Descrição |
|---|---|
| `w(t)` | Ruído branco Gaussiano ~ N(0,1) |
| `BPF{·}` | Filtro passa-banda 20–450 Hz (Butterworth 4ª ordem) |
| `e(t)` | Envelope de contração (0 a 1) |
| `A` | Amplitude de pico em Volts |

### 2.1 Ruído Branco Gaussiano

O ruído branco `w(t)` possui densidade espectral de potência (PSD) plana em toda a
banda de frequências. Ao ser filtrado pelo passa-banda, o sinal resultante adquire a
coloração espectral característica do EMG, concentrando sua energia entre 20 e 450 Hz
[De Luca et al., 2010].

### 2.2 Filtro Passa-Banda 20–450 Hz

A banda de 20–450 Hz é a faixa fisiológica padrão do sEMG, conforme estabelecido
pela *Surface ElectroMyoGraphy for the Non-Invasive Assessment of Muscles* (SENIAM)
[Stegeman & Hermens, 2007].

**Especificações do filtro:**

| Parâmetro | Valor |
|---|---|
| Tipo | Butterworth |
| Ordem | 4ª (24 dB/oitava) |
| Passa-alta (fc1) | 20 Hz |
| Passa-baixa (fc2) | 450 Hz |
| Taxa de amostragem | 1000 Hz |

**Motivação das frequências de corte:**

- **20 Hz (passa-alta):** Remove componentes DC, artefatos de movimento e deriva
  da linha de base. Frequências abaixo de 20 Hz no EMG são dominadas por ruído de
  movimento e não por atividade muscular [De Luca et al., 2010].
- **450 Hz (passa-baixa):** A energia do sEMG acima de 450 Hz é desprezível para
  a maioria dos músculos, além de evitar *aliasing* (teorema de Nyquist: fs/2 = 500 Hz).

**Resposta em frequência:**

O filtro Butterworth de 4ª ordem oferece uma atenuação de −24 dB/oitava fora da
banda de passagem, com resposta plana na banda passante (sem ripple), garantindo
que o sinal gerado não sofra distorções espectrais artificiais.

### 2.3 Envelope de Contração

O envelope `e(t)` modela a **ativação muscular** ao longo do tempo, representando
o recrutamento progressivo de unidades motoras. É composto por cinco fases:

```
e(t) = e_rest(t) + e_ramp_up(t) + e_hold(t) + e_ramp_down(t) + e_rest(t)
```

```
Amplitude
  1.0 |         ┌──────────────────┐
      |        /                    \
      |       /                      \
      |      /                        \
  0.0 |─────┘                          └─────────
      └───────────────────────────────────────────→ t
      0s   0.5s   1.1s        1.9s     2.5s    3.0s
      ↑     ↑      ↑            ↑        ↑       ↑
      |     |      |            |        |       └─ repouso final
      |     |      |            |        └── rampa descida (curva x²)
      |     |      |            └─── sustentação (constante)
      |     |      └── rampa subida (curva x¹·⁵)
      |     └── repouso inicial
      └── t=0
```

**Justificativa das formas:**

- **Rampa de subida (`x¹·⁵`):** O recrutamento de unidades motoras segue o
  *princípio do tamanho* de Henneman — unidades menores (tipo I) recrutadas primeiro,
  seguidas por unidades maiores (tipo II). Isso produz uma relação não-linear entre
  ativação neural e força muscular [Henneman et al., 1965]. A curva `x¹·⁵` modela
  esta não-linearidade de forma simplificada.
- **Sustentação (`constante`):** Contração isométrica sustentada com recrutamento
  estável — condição típica de testes de força máxima ou submáxima.
- **Rampa de descida (`x²`):** O relaxamento muscular é mais rápido que a ativação
  (devido ao bombeamento de Ca²⁺ para o retículo sarcoplasmático), modelado por
  uma curva quadrática [Westerblad & Allen, 2002].

### 2.4 Amplitude de Pico

A amplitude `A` define o nível máximo do sinal EMG durante a contração sustentada.
O valor padrão é **±1,5 mV** (1500 µV de pico), consistente com a faixa típica do
sEMG de superfície em contrações máximas de músculos médios (100–3000 µV pico-a-pico,
dependendo do músculo, posição dos eletrodos e nível de contração) [Konrad, 2005].

**Faixas típicas de amplitude sEMG:**

| Músculo | Atividade | Amplitude típica (pico-a-pico) |
|---|---|---|
| Bíceps braquial | Contração máxima | 2–5 mV |
| Extensor dos dedos | Contração submáxima | 0,5–2 mV |
| Músculos intrínsecos da mão | Preensão | 0,2–1 mV |
| Face (orbicular) | Atividade leve | 50–200 µV |

## 3. Validação do Sinal Gerado

### 3.1 Características preservadas

O sinal gerado reproduz as seguintes propriedades do sEMG real:

| Propriedade | sEMG real | Gerador sintético |
|---|---|---|
| Banda espectral | 20–450 Hz | 20–450 Hz (Butterworth 4ª) |
| Distribuição de amplitude | ~ Gaussiana (contração) | Gaussiana (ruído filtrado) |
| Forma de onda | Bifásica | Bifásica |
| Envelope de ativação | Variável | Programável |
| Resolução | 16 bits típica | 16 bits |

### 3.2 Limitações

O modelo de ruído filtrado não reproduz:

- **Forma individual de MUAPs:** Diferentemente de modelos baseados em disparos de
  unidades motoras (ex: modelo de Hamilton-Wright & Stashuk, 2005), o sinal gerado
  não contém a forma característica tripásica de cada MUAP.
- **Fenômeno de fadiga:** O deslocamento espectral para baixas frequências (compressão
  do espectro) observado em contrações sustentadas não é modelado.
- **Interferência de 50/60 Hz:** Ruído de rede elétrica não é adicionado, pois
  assume-se que o módulo de aquisição sob teste já possui notch filter.

## 4. Formatos de Saída

O sinal é exportado em três formatos:

### 4.1 int16 (DAC externo)

O sinal em Volts é escalado para o range do DAC de 16 bits (±1 V):

```
Código_int16 = (V_emg / V_ref_DAC) × 32767
V_ref_DAC = ±1,0 V
```

Range: [−32768, 32767] corresponde a [−1,0 V, +1,0 V] na saída do DAC.

### 4.2 uint12 (DAC interno MCU)

O sinal é amplificado (ganho G = 200) e deslocado para o range 0–3,3 V:

```
V_centrado = V_emg × G + V_offset
Código_uint12 = (V_centrado / 3,3) × 4095
G = 200, V_offset = 1,65 V
```

O atenuador externo reduz o sinal de volta para amplitudes fisiológicas antes de
injetá-lo no módulo de aquisição sob teste.

### 4.3 Raw binário

Os valores int16 são gravados em little-endian, prontos para transferência por DMA.

## 5. Referências

1. **De Luca, C. J., et al.** (2010). "Filtering the surface EMG signal: Movement
   artifact and baseline noise contamination." *Journal of Biomechanics*,
   43(8), 1573–1579. DOI: [10.1016/j.jbiomech.2010.01.027](https://doi.org/10.1016/j.jbiomech.2010.01.027)

2. **Farina, D., & Merletti, R.** (2004). "Estimation of average muscle fiber
   conduction velocity from two-dimensional surface EMG recordings."
   *Journal of Neuroscience Methods*, 134(2), 199–208.
   DOI: [10.1016/j.jneumeth.2003.10.004](https://doi.org/10.1016/j.jneumeth.2003.10.004)

3. **Henneman, E., Somjen, G., & Carpenter, D. O.** (1965). "Functional significance
   of cell size in spinal motoneurons." *Journal of Neurophysiology*, 28(3), 560–580.
   DOI: [10.1152/jn.1965.28.3.560](https://doi.org/10.1152/jn.1965.28.3.560)

4. **Konrad, P.** (2005). *The ABC of EMG: A Practical Introduction to
   Kinesiological Electromyography*. Noraxon Inc.

5. **Nawab, S. H., Chang, S. S., & De Luca, C. J.** (2010). "High-yield
   decomposition of surface EMG signals." *Clinical Neurophysiology*,
   121(10), 1602–1615. DOI: [10.1016/j.clinph.2009.11.092](https://doi.org/10.1016/j.clinph.2009.11.092)

6. **Stegeman, D. F., & Hermens, H. J.** (2007). "Standards for surface
   electromyography: The European project 'SENIAM'." In *Electromyography:
   Physiology, Engineering, and Non-Invasive Applications* (pp. 107–127).
   IEEE Press. DOI: [10.1002/0471678384.ch7](https://doi.org/10.1002/0471678384.ch7)

7. **Westerblad, H., & Allen, D. G.** (2002). "Changes in myoplasmic calcium
   concentration during fatigue." *Advances in Experimental Medicine and Biology*,
   538, 419–429. DOI: [10.1007/978-1-4419-9029-7_38](https://doi.org/10.1007/978-1-4419-9029-7_38)

8. **Hamilton-Wright, A., & Stashuk, D. W.** (2005). "Physiologically based
   simulation of clinical EMG signals." *IEEE Transactions on Biomedical
   Engineering*, 52(2), 171–183. DOI: [10.1109/TBME.2004.840510](https://doi.org/10.1109/TBME.2004.840510)

9. **Merletti, R., & Parker, P. A.** (2004). *Electromyography: Physiology,
   Engineering, and Non-Invasive Applications*. Wiley-IEEE Press.
   ISBN: 978-0-471-67580-8
