# Vozes da narração

- `homem_ref.wav` – referência da voz masculina (desde 14/11/2026): fala sintética gerada pelo Kokoro-82M (licença Apache 2.0),
  voz pt-BR "pm_alex", mais natural que a anterior. O Chatterbox usa este áudio só como molde de timbre. Nenhuma pessoa real.
- `homem_ref_piper_antigo.wav` – referência anterior (Piper "cadu"), soava robótica; mantida só para histórico.
- Ajustes para soar humano (pedido do titular, 14/11/2026): sem mudança de tom (pitch 1.0), exaggeration 0.7, cfg 0.35, sem aceleração.
- Voz feminina: voz padrão embutida no modelo Chatterbox Multilingual (sintética).
- A voz do titular NÃO fica aqui: este repositório é público. Só usar se ele pedir, com a amostra guardada em local privado.
- **18/11/2026 – vozes reais autorizadas (decisão do titular):** um homem e uma mulher gravam ~30 s cada, com autorização por
  escrito. As amostras NÃO entram neste repositório público: ficam no Google Drive do escritório e são baixadas para /tmp na hora
  de gerar, apontadas por `REELS_VOZ_MULHER_REF` e `REELS_VOZ_HOMEM_REF`. Sem essas variáveis, o `reels.py` usa as referências antigas.
