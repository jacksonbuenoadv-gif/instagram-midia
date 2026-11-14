# Banco de vídeos para os Reels

Vídeos gratuitos do Pexels (licença Pexels: uso livre, inclusive comercial, sem obrigação de crédito).
Reduzidos para 720x1280, 30 fps, sem áudio. Use o nome do arquivo sem `.mp4` no campo `clip` do spec.

| arquivo | o que mostra | bom para | Pexels id |
|---|---|---|---|
| dor_homem_careta | homem careca fazendo careta de dor, céu azul | gancho de dor (qualquer tema) | 7299358 |
| dor_lombar_maos_nas_costas | mulher com as mãos na lombar | dor nas costas, coluna, hérnia | 7299336 |
| dor_pescoco_computador | rapaz com dor no pescoço no notebook | LER/DORT, escritório, pescoço, ombro | 27430390 |
| motorista_sentado_cabine | entregador sentado na cabine de uma van | horas sentado, motorista | 6405950 |
| caminhao_passando_ceu_azul | carreta branca passando, céu azul | vibração, estrada, caminhoneiro | 35210503 |
| carreta_trabalhador_ajustando | trabalhador mexendo embaixo da carreta | carga e descarga, esforço | 35210505 |
| caminhao_por_do_sol_frente | caminhão vindo de frente no pôr do sol, faróis | CAPA de temas de caminhoneiro | 34479229 |
| estrada_pb_caminhoes | rodovia em preto e branco com caminhões | fundo desfocado dos cartões | 37335702 |
| caminhao_vermelho_rodovia | caminhão vermelho em rodovia urbana | estrada, trânsito, acidente de trajeto | 36456221 |
| caminhao_branco_manobra | cavalo mecânico branco manobrando | pátio, carga | 33870727 |

Para ampliar o banco: `python3 ferramentas/reels/baixar_clip.py <link do Pexels> <nome> "<o que mostra>" "<bom para>"`
(baixa, reduz para 720x1280/30 fps sem áudio e acrescenta a linha nesta tabela). Exige acesso a www.pexels.com e videos.pexels.com;
sem isso, baixe pelo navegador do app desktop e reduza com
ffmpeg -vf "fps=30,scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280" -an -crf 25.
Regra de uso (14/11/2026): nenhum clipe repetido no mesmo Reels nem usado nos 2 Reels anteriores — ver COMO_FAZER.md, seção 3.1. Faltam hoje: ambiente de fábrica/máquinas, obra/queda, moto, fone/ruído, mãos com formigamento.
