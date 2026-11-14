# Reels semanal do @jacksonbueno.adv — passo a passo

Um Reels por semana, publicado às **12h (horário de Brasília)**, e um **story às 18h** do mesmo dia avisando do Reels.
Português do Brasil, linguagem simples, sem juridiquês. O titular revisa depois e avisa se algo precisar mudar.

## Padrão visual aprovado pelo titular (12/11/2026) — não mudar sem ele pedir
- **Respiro nas laterais:** nenhum elemento inserido (cartões, faixas, títulos, listas, checklist, caixa do site, selo, etiquetas) chega a menos de 150 px das bordas (`MX = 150` em `reels.py`).
- **Elementos discretos, não gigantes:** títulos de impacto com no máximo ~104 px de fonte (capa e gancho), ~76 px nos cartões e frases de destaque. Não aumente esses tamanhos; se um texto não couber, encurte ou quebre em duas linhas.
- **Legendas animadas:** o tamanho atual (54 px, largura total) está aprovado — não mexer.
- **Capa:** vídeo de banco em destaque (caminhão, máquina, situação) e a foto do titular só no selo redondo pequeno à direita; "DOENÇA DO TRABALHO" (ou a frase equivalente) no tamanho moderado do padrão, nunca de borda a borda.
- Ao conferir as prévias, reprove qualquer quadro em que algo encoste nas laterais ou pareça grande demais.

## Narração (orientação do titular de 12/11/2026, até ele mudar)
- Use **duas vozes sintéticas, uma mulher e um homem** — nunca a voz do titular.
- No spec: `"voz": "dupla"` no topo e, em cada cena, `"voz": "mulher"` ou `"voz": "homem"`, montando um bate-papo:
  a mulher costuma puxar o assunto (gancho, perguntas, situações do dia a dia, "o que fazer") e o homem responde/explica
  (resposta da capa, direitos, encerramento com o site). Evite a mesma voz em mais de 2 cenas seguidas.
- Cada frase é conferida automaticamente por transcrição e refeita se sair errada (ver log "voz ... tentativa").
  Se no log uma palavra importante continuar errada depois das tentativas, troque a palavra por um sinônimo simples e gere de novo.
- A narração com essas vozes leva ~10 min no total (modelo roda em CPU). A primeira execução instala o modelo (~3 GB).

## 1. Tema (sempre o nicho)
- Sempre **acidente de trabalho** ou **doença ocupacional**. Alterne: se o último Reels (pasta `reels/`) foi de doença, faça acidente, e vice-versa.
- Não repita o tema dos últimos 8 Reels.
- Escolha pelo que as pessoas **perguntam e buscam**: veja `dados/pautas_search_console.md` e faça 2–3 WebSearch para ver como a pergunta aparece no Google ("dor nas costas pode ser doença do trabalho", "formigamento na mão é LER", "zumbido no ouvido trabalho barulho", "depressão por causa do trabalho tem direito", "acidente no caminho do trabalho", "machucou a mão na máquina", "caí no trabalho e agora"...).
- Doença ocupacional: fale com as palavras do povo — **dor, dor nas costas, dor no ombro, dor no punho, formigamento, dormência, mão inchada, barulho, zumbido, surdez, cansaço, insônia, depressão, ansiedade, crise de pânico, burnout, falta de ar, alergia na pele**. Use o nome técnico só como apoio ("LER", "hérnia de disco").
- Acidente: queda, corte, máquina que prendeu a mão, choque, acidente de moto/carro no trajeto, acidente com caminhão, esmagamento, queimadura.
- Público: trabalhador comum (motorista, operador de máquina, pedreiro, auxiliar de produção, enfermagem, telemarketing, caixa...). De vez em quando, caminhoneiros.

## 2. Verdade
Toda afirmação jurídica precisa estar certa. Confirme em fonte primária (planalto.gov.br, gov.br/inss, tst.jus.br, stf.jus.br) antes de usar.
Base usual: Lei 8.213/91 arts. 19, 20, 21 (doença do trabalho, concausa, acidente de trajeto) e 118 (estabilidade de 12 meses); 22 (CAT);
art. 86 (auxílio-acidente); Lei 8.036/90 art. 15 §5º (FGTS no afastamento); Tema 932 do STF (responsabilidade objetiva em atividade de risco);
Portaria GM/MS 1.999/2023 (lista de doenças relacionadas ao trabalho, inclui ansiedade, depressão e burnout).

## 3. Roteiro (spec.json)
Crie `reels/<AAAA-MM-DD>/spec.json` seguindo o modelo `reels/2026-11-12/spec.json` (os tipos de cena e campos estão no cabeçalho de `ferramentas/reels/reels.py`).
- 45 a 60 s, 9 a 12 cenas. Frases curtas e faladas ("Você sente formigamento na mão?"), nada de termos difíceis.
- Estrutura que funciona:
  1. `hook` (0–3 s): vídeo de dor/situação + pergunta gigante que a pessoa se faz ("FORMIGAMENTO NA MÃO?", "CAIU NO TRABALHO?").
  2. `cover`: a resposta curta que gera curiosidade ("pode ser DOENÇA DO TRABALHO"). **Regra da capa: vídeo de banco em destaque (caminhão, máquina, situação) e a foto do titular só no selo redondo menor** (`badge`). O último quadro desta cena vira `capa.jpg`.
  3. `montage`: 3 situações do dia a dia que causam o problema.
  4. 3–4 `card`: sintomas, doenças ou tipos de acidente, com emoji.
  5. `statement`: o ponto que surpreende e faz compartilhar ("não precisa ser a única causa", "acidente no caminho também conta", "mesmo sem CAT você pode...").
  6. `list`: direitos (B91, 12 meses de estabilidade, FGTS, indenização, auxílio-acidente...).
  7. `check`: o que fazer agora (médico/exames, CAT, guardar provas...).
  8. `cta`: "Quer entender o seu caso? Acesse jacksonbueno.adv.br" + "Envie para <quem precisa ver>".
- Clipes: veja a seção "Vídeos" logo abaixo. Faça a busca de clipes ANTES de escrever o spec.
- `key` = palavra do texto narrado no momento em que a animação deve aparecer.
- Não esqueça `"voz": "dupla"` no topo e `"voz"` em cada cena (ver "Narração").

## 3.1 Vídeos — sem repetir (pedido do titular, 14/11/2026)
- **Regra (atualizada pelo titular em 14/11/2026):** nenhum clipe aparece duas vezes no mesmo Reels, e um clipe só pode voltar
  **90 dias (cerca de 3 meses) depois do último uso** (o fundo desfocado padrão dos cartões não conta). O `reels.py` confere isso sozinho e para com erro se a regra for quebrada.
- **Busca antes de cada Reels (obrigatória):**
  1. Liste as cenas que precisam de vídeo (gancho, capa, 3 da montagem; `bg_clip` dos cartões se quiser variar) e o que cada uma deve mostrar,
     de acordo com o tema (moto, trânsito, fábrica, obra, escritório, mãos, ombro, barulho, hospital...).
  2. Veja no `ferramentas/reels/stock/README.md` o que já existe e não foi usado nos últimos 90 dias
     (`grep -o '"clip": "[a-z_]*"' reels/*/spec.json` mostra o histórico).
  3. Para o que faltar (ou se o clipe disponível não combinar bem com o tema), busque no Pexels com WebSearch, termos em inglês:
     `site:pexels.com/video motorcycle traffic vertical`, `site:pexels.com/video factory worker machine`, `... back pain`, `... construction worker`.
     Prefira vídeos verticais, sem marca d'água, sem logotipo de empresa em destaque e sem acidente explícito/sangue.
  4. Baixe e registre cada um: `python3 ferramentas/reels/baixar_clip.py <link do Pexels> <nome_do_clipe> "<o que mostra>" "<bom para>"`.
     Abra com Read o quadro `stock/_conferir_<nome>.jpg`; se não servir, apague o .mp4 e a linha do README. Apague os `_conferir_*.jpg` antes do commit.
  5. Aproveite e guarde mais 5 a 8 clipes do nicho para os próximos Reels: com 2 Reels por semana e a janela de 90 dias,
     o banco precisa de pelo menos ~150 clipes para nunca faltar. Commit dos clipes novos junto com o Reels.
- **Se a busca ou o download falharem** (domínio bloqueado nesta sessão): use só clipes do banco, sem repetir dentro do Reels.
  Se não houver clipes inéditos suficientes, gere com `--permitir-repetidos` e acrescente à notificação final
  "(vídeos repetidos: não consegui baixar clipes novos — liberar pexels.com nas configurações)".

## 4. Legenda (copy)
Curta, fácil de ler, com ícones e hashtags. Modelo:
```
<emoji> <pergunta/gancho com a palavra que as pessoas buscam>!

<1–2 frases simples explicando> <emoji>

⚠️ <lista curta com emojis>
...

✅ <o ponto principal>

Você pode ter direito a:
➡️ ...

📌 Salve e mande pra quem precisa ver.
🌐 jacksonbueno.adv.br

#acidentedetrabalho #doencaocupacional #<5 a 7 hashtags específicas em português>
```
Coloque a legenda no campo `"legenda"` do spec.

## 5. Gerar e conferir
```
cd ferramentas && npm i -s @fontsource/montserrat && cd ..
python3 ferramentas/reels/reels.py reels/<data>/spec.json reels/<data> --preview
```
Abra com Read `reels/<data>/capa.jpg`, `story.jpg` e cada quadro de `reels/<data>/preview/`: texto inteiro na tela, nada cortado, português correto, rosto do titular sem texto por cima, e o padrão visual acima respeitado (margens de respiro, elementos discretos). Corrija o spec e repita se preciso. Depois:
```
python3 ferramentas/reels/reels.py reels/<data>/spec.json reels/<data>
```
Apague `reels/<data>/preview/` antes do commit (não versionar).

## 6. Publicar (12h)
1. Commit (autor "Claude", noreply@anthropic.com) e push para main de `reel.mp4`, `capa.jpg`, `story.jpg`, `legenda.txt`, `spec.json`.
2. Confirme com curl que `https://raw.githubusercontent.com/jacksonbuenoadv-gif/instagram-midia/main/reels/<data>/reel.mp4` e `.../capa.jpg` respondem 200.
3. Espere até 12:00 (America/Sao_Paulo) se ainda não for a hora.
4. Windsor `execute_action`: connector `instagram`, account `17841443412861408`, action `create_video_post`,
   params `{"video_url": "<link do reel.mp4>", "cover_url": "<link da capa.jpg>", "caption": "<legenda.txt>", "share_to_feed": true}`.
   Se o Instagram recusar o link do raw.githubusercontent, tente o mesmo arquivo por `https://cdn.jsdelivr.net/gh/jacksonbuenoadv-gif/instagram-midia@main/reels/<data>/reel.mp4`.
5. Grave `reels/<data>/publicado.txt` com o media id e o horário, commit e push. Envie PushNotification "Reels publicado: <tema>".
6. O `story.jpg` fica no repositório para a tarefa das 18h.

Se algo falhar: envie `reel.mp4`, `capa.jpg` e `legenda.txt` com SendUserFile e PushNotification "Reels pronto, mas não publicado (<motivo curto>)".
