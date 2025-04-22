# 🎓 Educational Video Downloader

**Automacao com Selenium • Engenharia reversa de `.m3u8` • Manipulacao de mídia com FFmpeg**

Este projeto nasceu como uma solução improvisada e se transformou em um laboratório completo de automação web, raspagem de conteúdo e manipulação de vídeos — tudo feito com **Python** (e bastante teimosia).

---

## ✨ Motivação

Quando minha assinatura de uma plataforma educacional estava prestes a vencer (e eu sem condições de renovar), decidi criar esta ferramenta para garantir que meus estudos não fossem interrompidos. A plataforma exigia login, mas não oferecia download dos vídeos — e o plano vitalício custava 4x o valor da assinatura anual.

O resultado? Duas semanas de experimentos com:

- Selenium para automação de login
- Engenharia reversa de players `.m3u8`
- FFmpeg para concatenação de vídeos
- Logging, modularização e persistência de sessão com cookies

Este repositório é o produto final, com estrutura reutilizável e código comentado.

> 💡 Foi tanto um aprendizado técnico quanto um ato de resistência.

---

## ⚙️ Tecnologias Utilizadas

- **Python 3.11** (com _type hints_ onde possível)
- `Selenium` + `webdriver-manager` — login automatizado
- `BeautifulSoup` — parsing de HTML para extrair metadados
- `Requests` — acesso a páginas e streams
- `FFmpeg` — download e concatenação dos segmentos `.ts`
- `Tqdm` — barra de progresso no terminal
- `Markdownify` — fallback para salvar aulas como `.md` se não houver vídeo

---

## 📁 Estrutura do Projeto

```
.
├── main.py                      # Ponto de entrada com menu CLI
├── downloader/                  # Pacote com módulos especializados
│   ├── auth.py                  # Login e gestão de sessão
│   ├── extract_m3u8.py          # Extração da melhor stream de vídeo
│   ├── lessons.py               # Lógica para baixar aulas e cursos
│   ├── parser.py                # Extração de iframe e título
│   ├── utils.py                 # Funções auxiliares (ex: sanitização de nomes)
│   └── video_downloader.py      # Download segmentado + concatenação
├── downloads/                   # Pasta padrão de saída
├── .config/                     # Sessão salva com cookies (gitignorada)
└── requirements.txt             # Dependências
```

---

## 🚀 Como Usar

1. **Instale as dependências:**

```bash
pip install -r requirements.txt
# Certifique-se também de que o FFmpeg está instalado no sistema:
# Linux: sudo apt install ffmpeg
# MacOS: brew install ffmpeg
# Windows: choco install ffmpeg
```

2. **Execute o script principal:**

```bash
python main.py
```

- Você será solicitado a informar seu e-mail e senha da plataforma.
- Os dados de sessão serão salvos localmente (`.config/`) se desejar.
- Escolha uma das opções:
  - Baixar aula única
  - Baixar lista de aulas
  - Baixar curso completo

---

## 🧐 Lições e Arquitetura

- **Evolução:** Começou como script monolítico → evoluiu para arquitetura modular
- **Foco:** MVP funcional rápido, com espaço para melhorias incrementais
- **Organização:** Separação clara entre automação (login), extração (parser) e manipulação de vídeo (download)

---

## ⚠️ Aviso Legal

Este projeto **não contorna DRM**, não acessa conteúdo protegido indevidamente e **não deve ser usado para violar os termos de uso de nenhuma plataforma**.

Use-o apenas para baixar conteúdos **aos quais você tem acesso legítimo**.

Você é responsável por como utiliza este código.

---

## 📬 Contato

Se você também está reinventando sua carreira com código, automação e IA, vamos trocar ideias!

Me chama no [LinkedIn](https://linkedin.com/) ou deixe um comentário no post sobre este projeto.

---

