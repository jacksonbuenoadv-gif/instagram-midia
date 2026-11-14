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
| moto_entregador_rua_costas | entregador de scooter saindo pela rua (de costas) | acidente de trajeto, moto, motoboy | 7362642 |
| motoboy_pacote_moto | motoboy de camiseta vermelha ajeitando pacote na moto | motoboy, entregador, trajeto | 6867868 |
| scooter_vindo_frente | entregador de scooter vindo de frente na rua | moto, acidente de trajeto, gancho | 7362651 |
| moto_rua_entardecer | homem pilotando moto em rua no fim de tarde | moto, trajeto, volta pra casa | 4922702 |
| avenida_taxis_moto | avenida movimentada com carros e moto, vista de cima | trânsito, acidente de trajeto | 4834901 |
| pedestres_faixa_semaforo | pedestres atravessando na faixa com semáforo | atropelamento, trajeto a pé | 5631418 |
| onibus_passageiros_dentro | passageiros sentados dentro de ônibus | trajeto de ônibus, queda no ônibus | 4426194 |
| onibus_corredor | corredor de ônibus urbano | ônibus, trajeto | 29579253 |
| onibus_lotado_escuro | ônibus lotado com gente em pé, contraluz | ônibus cheio, trajeto, cansaço | 30424343 |
| fabrica_operario_inspecao | operário concentrado conferindo peças na fábrica | fábrica, LER, esforço repetitivo | 32244734 |
| fundicao_faiscas | operário em fundição com faíscas | calor, queimadura, indústria pesada | 5121742 |
| costura_maos_maquina | mãos operando máquina de costura industrial | costureira, LER, punho, formigamento | 18092534 |
| soldador_faiscas | soldador de máscara com faíscas | solda, queimadura, olhos, fumos | 34771890 |
| soldador_oficina | soldador trabalhando na oficina | metalúrgico, solda, barulho | 14314645 |
| obra_escoras_peao | trabalhador de colete e capacete montando escoras na obra | pedreiro, obra, queda | 36601732 |
| obra_ferragem_laje | operários sobre ferragem de laje, vista de cima | obra, queda de altura | 35631533 |
| obra_equipe_concreto | equipe de capacete concretando laje | obra, pedreiro, esforço | 13921040 |
| obra_peao_abaixado | trabalhador de colete abaixado na obra | coluna, esforço, obra | 10294766 |
| armazem_caixa_pesada | homem carregando caixa no armazém | peso, dor nas costas, hérnia | 4292578 |
| carregando_caixas | homens carregando caixas | carga e descarga, coluna | 4296840 |
| entregadora_caixa | mulher levando caixa na rua | carregar peso, entrega | 6169117 |
| britadeira_obra_rua | operário com britadeira atrás de grades na rua | barulho, perda auditiva, zumbido | 6719463 |
| britadeira_close | britadeira quebrando asfalto (close) | barulho, vibração, zumbido | 855956 |
| telemarketing_headset | atendente com headset no computador | telemarketing, LER, ansiedade | 7707061 |
| digitando_teclado_maos | mãos digitando no teclado | LER, tendinite, escritório | 3254071 |
| maos_massagem_dor | mãos massageando os dedos | dor nas mãos, formigamento, LER | 4457845 |
| medico_consulta | médico atento em consulta | médico, atestado, exames | 4352136 |
| medico_paciente_mascara | médico de máscara atendendo paciente | consulta, perícia, exames | 8413486 |
| medica_exames_papel | médica analisando exames na mesa | exames, laudo, atestado | 7579338 |
| trabalhador_estresse_maos | homem estressado com as mãos na cabeça no trabalho | ansiedade, burnout, depressão | 7640684 |
| homem_cabeca_nas_maos | homem sentado com a cabeça nas mãos | depressão, crise de pânico, burnout | 8555702 |

Para ampliar o banco: `python3 ferramentas/reels/baixar_clip.py <link do Pexels> <nome> "<o que mostra>" "<bom para>"`
(baixa, reduz para 720x1280/30 fps sem áudio e acrescenta a linha nesta tabela). Exige acesso a www.pexels.com e videos.pexels.com;
sem isso, baixe pelo navegador do app desktop e reduza com
ffmpeg -vf "fps=30,scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280" -an -crf 25.
Regra de uso (14/11/2026): nenhum clipe repetido no mesmo Reels; um clipe só volta 90 dias depois do último uso — ver COMO_FAZER.md, seção 3.1.
