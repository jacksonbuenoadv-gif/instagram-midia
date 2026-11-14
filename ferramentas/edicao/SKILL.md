---
name: edicao-ilustrada-jackson-bueno
description: Use quando o Dr. Jackson Bueno (@jacksonbueno.adv, acidente de trabalho e doença ocupacional) enviar um vídeo gravado por ele para editar no estilo "edição dinâmica" para Reels/TikTok: cortes de pausas, zooms, legendas animadas, ilustrações (b-roll, ícones, cartões) que aparecem quando a palavra é falada, efeitos sonoros, trilha, capa e legenda do post, com foco em crescer o Instagram e levar gente ao site.
---

# Edição ilustrada dos vídeos do Dr. Jackson Bueno

Objetivo de todo vídeo: **a pessoa se reconhecer nos primeiros 2 segundos, assistir até o fim, mandar para alguém e seguir o perfil**,
e depois ir ao site jacksonbueno.adv.br. A edição serve à mensagem: ágil, mas limpa e confiável (é um advogado).
Português do Brasil, linguagem do povo. Toda afirmação jurídica precisa ser verdadeira (confirme em fonte primária).

## 0. Antes de começar
- Repositório `jacksonbuenoadv-gif/instagram-midia` (clone/pull). Leia `VISIBILIDADE.md` (regra universal: aparecer nas buscas do
  Google, das IAs e das redes) e, se existir, `dados/desempenho.md` (o que está funcionando).
- Ferramentas: `ferramentas/edicao/editar.py` (se ainda não existir, crie seguindo a seção "Implementação" e salve no repositório),
  banco de vídeos `ferramentas/reels/stock/` (+ `baixar_clip.py` para buscar no Pexels), fontes e cores de `ferramentas/reels/reels.py`.
- Pasta do trabalho: `videos/AAAA-MM-DD-<tema-curto>/` com `bruto.mp4` (original, NÃO versionar se > 50 MB), `plano.json`, `final.mp4`,
  `capa.jpg`, `legenda.txt`.

## 1. Entender o vídeo
1. Transcreva com tempo por palavra (faster-whisper, modelo "small" ou "medium", `word_timestamps=True`, idioma pt).
2. Marque: silêncios > 0,35 s, "ééé/tipo/né" soltos, frases repetidas (fica o último take bom), tropeços.
3. Identifique o tema, a pergunta principal e as palavras-chave (sintomas, profissões, benefícios, leis).
4. Confira cada afirmação jurídica. Se algo estiver errado ou arriscado, NÃO edite por cima: avise o titular e sugira regravar o trecho.

## 2. Plano de edição (`plano.json`) — mostre um resumo ao titular antes de renderizar se ele estiver presente
Estrutura que deve sair do vídeo (reordene trechos se ajudar, sem mudar o sentido):
- **Gancho (0–2 s):** a frase mais forte ou a pergunta do povo ("Sua coluna dói por causa do serviço?"). Texto grande na tela +
  push-in lento + som de impacto. Se o vídeo começar fraco, puxe para o início o melhor trecho (ou o próprio resultado).
- **Promessa (2–5 s):** por que assistir até o fim ("em 40 segundos você sabe se tem direito").
- **Conteúdo (3 pontos no máximo):** um ponto por bloco, cada bloco com uma ilustração.
- **Virada:** o fato que surpreende e faz compartilhar ("não precisa ser a única causa", "vale até sem CAT").
- **Chamada final:** UMA ação principal, variando: "Segue pra não perder a parte 2", "Manda pra quem trabalha de moto",
  "Salva pra mostrar no médico", "Comenta a sua profissão que eu faço um vídeo pra ela". E o site na tela: jacksonbueno.adv.br.

## 3. Ritmo, cortes e zoom
- Corte seco (jump cut) em todos os silêncios e muletas; deixe 0,08 s de respiro antes da fala para não soar robótico.
- **Mude algo na tela a cada 2–4 s**: zoom, b-roll, cartão, ícone, troca de enquadramento. Nada de mais de 5 s parado igual.
- Zoom: alternar enquadramento normal (100%) e aproximado (112–120%) a cada corte; **punch-in rápido (0,15 s)** nas palavras de
  impacto; **push-in lento** (100→108% ao longo do trecho) no gancho e na virada. Sempre centralizado no rosto; nunca cortar olhos/boca.
- B-roll ocupa a tela toda por 1–2,5 s ou aparece em janela (picture-in-picture) no terço superior, com a voz dele continuando.
- Transições só por corte, zoom ou "whip" rápido. Nada de efeitos de template (estrela, cubo, glitch exagerado).

## 4. Ilustrações (o que aparece quando ele fala)
Cada palavra-chave ganha um elemento no exato momento em que é dita (pelo tempo da transcrição):
- **Palavra em destaque** (até 3 palavras, 76–104 px, âmbar #FFBA30 sobre faixa escura), com "pop" de escala.
- **Ícone/emoji** grande (🦴 coluna, ✋ punho/mão, 👂 zumbido, 🧠 ansiedade, 🏍️ moto, 🚌 ônibus, 📄 CAT, 🏥 INSS, ⚖️ lei).
- **Cartão de lei** discreto no rodapé do quadro ("Lei 8.213/91, art. 118") quando ele citar a regra.
- **Checklist** que vai sendo marcado quando ele lista o que fazer.
- **B-roll de identificação**: o público precisa se ver. Use profissões e cenas do público (motoboy, pedreiro, operador de máquina,
  auxiliar de produção, caixa, telemarketing, enfermagem, motorista de ônibus/caminhão, faxineira), mãos calejadas, EPI, ônibus lotado,
  fila, receita/atestado, raio-x. Prefira cenas com cara de Brasil. Evite: executivos de terno, escritório de luxo, modelos sorrindo
  sem motivo, sangue/acidente explícito, logotipos de empresas.
- Regra de vídeos de banco: nenhum clipe repetido no mesmo vídeo e nenhum clipe usado nos últimos 90 dias (mesma regra dos Reels;
  confira `reels/*/spec.json` e `videos/*/plano.json`). Falta clipe? Busque no Pexels e baixe com `baixar_clip.py`.
- Nunca cubra o rosto dele com texto. Margem lateral de 150 px. Zona segura do Instagram: nada importante nos 220 px de cima nem
  nos 420 px de baixo (botões e legenda do app).

## 5. Legendas
- Legenda animada sempre (muita gente assiste sem som): 2–4 palavras por vez, fonte Montserrat 800, 54 px, branca com contorno/sombra,
  **palavra-chave em âmbar** no momento em que é dita. Posição: terço inferior, acima da zona segura, sem cobrir a boca.
- Corrija a transcrição (nomes, siglas: INSS, CAT, B91, LER/DORT; "jacksonbueno.adv.br").

## 6. Som
- Voz: limpe ruído leve (afftdn), corte graves < 80 Hz, normalize para cerca de −14 LUFS. A voz manda: tudo o resto fica embaixo dela.
- Trilha instrumental original e discreta (gere com `ferramentas/trilha.py` ou o `make_music` do reels.py), −26 a −30 dB abaixo
  da voz, com ducking. Nunca use música comercial com direitos.
- Efeitos sonoros curtos e baixos, sintetizados (sem banco com direitos): **whoosh** nas entradas de b-roll, **pop** em textos e
  ícones, **ding/clique** no checklist, **riser** de 1 s antes da virada, **impacto grave** no gancho. Máximo de 1 efeito a cada 2 s.

## 7. Capa (`capa.jpg`, 1080x1920)
- O rosto dele com expressão viva (escolha o melhor quadro: olhos abertos, boca fechada ou falando com ênfase) + 3 a 6 palavras
  grandes com a pergunta do povo ("DOR NAS COSTAS DÁ DIREITO?"). Tudo importante dentro do centro 1080x1440 (o perfil corta em 3:4).
- Mesma identidade das outras capas (azul-marinho #0A1424, âmbar #FFBA30, Montserrat), para o perfil ficar reconhecível.

## 8. Legenda do post (`legenda.txt`) — seguir `VISIBILIDADE.md`
Primeira linha = a pergunta com a palavra que as pessoas buscam; resposta direta em 1–2 frases com a base legal; 3–5 linhas com
ícones; chamada (seguir/enviar/salvar/comentar); "🌐 jacksonbueno.adv.br" e, se houver artigo no blog sobre o tema, "📖 artigo
completo no blog, link na bio"; assinatura "👨‍⚖️ Dr. Jackson Bueno · Advogado de acidente de trabalho e doença ocupacional ·
OAB/MG 211.217"; 4–7 hashtags (uma de serviço: #advogadoacidentedetrabalho ou #advogadodoencaocupacional).

## 9. Conferir e entregar
1. Gere prévias (quadros nos momentos-chave + um trecho de 10 s) e confira com Read: nada cortado, nada sobre o rosto,
   português correto, margens e zona segura respeitadas, ilustração aparecendo na palavra certa.
2. Render final: 1080x1920, 30 fps, H.264 (crf 18–20), AAC 192 kbps, duração ideal 30–75 s. Sem marca d'água de nenhum app.
3. Entregue `final.mp4`, `capa.jpg` e `legenda.txt` com SendUserFile. **Publique só se o titular pedir** (aí: commit/push e Windsor
   `create_video_post` com `cover_url`, como no guia dos Reels; depois o primeiro comentário com uma pergunta).
4. Registre em `videos/AAAA-MM-DD-<tema>/plano.json` os clipes usados (para a regra dos 90 dias) e o tema.

## 10. Orientação de gravação para o titular (mande quando ele perguntar como gravar)
Celular na vertical, na altura dos olhos, luz de frente (janela), microfone de lapela, fundo arrumado; olhar na lente; começar
direto pela pergunta; frases curtas; gravar o gancho 3 vezes de jeitos diferentes; 30–90 s de fala; pode errar e repetir a frase
(o corte resolve).

## Implementação (`ferramentas/edicao/editar.py`)
Python + ffmpeg + faster-whisper + Pillow, no mesmo estilo do `reels.py`: (1) transcrever com tempos por palavra; (2) montar a lista
de trechos mantidos (cortes); (3) para cada quadro, compor: vídeo do titular com zoom do plano → b-roll/janela → elementos gráficos
→ legenda; (4) áudio: voz tratada + trilha com ducking + efeitos nos tempos dos eventos; (5) `--preview` gera só quadros de conferência.
Entrada: `plano.json` com `cortes`, `zooms`, `eventos` [{tempo, tipo: texto|icone|lei|checklist|broll, ...}], `capa` {tempo, texto}.
