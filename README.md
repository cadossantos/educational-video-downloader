🎓 Educational Video Downloader
(Selenium • BeautifulSoup • M3U8 • FFmpeg)

Um projeto que começou como solução improvisada e virou um laboratório completo de automação web e manipulação de mídia — feito com Python e teimosia.

✨ Motivação
Quando a assinatura de uma plataforma educacional estava prestes a vencer (e eu, ainda desempregado, sem condições de renovar), decidi criar esta ferramenta para garantir que meus estudos continuassem. A plataforma permitia acesso via login, mas não oferecia downloads dos vídeos, para ter acesso completo, o plano vitalício custa aproximadamente 4x o valor do meu acesso anual :(

O resultado? Duas semanas de experimentos com Selenium, engenharia reversa de streams M3U8 e concatenação com FFmpeg — agora organizado neste repositório como um projeto modular e reutilizável.

Sim, foi tanto aprendizado técnico quanto ato de resistência.

⚙️ Tecnologias
Python 3.11 (com type hints onde possível)

Selenium para automação do login

BeautifulSoup para extração de metadados

Requests + FFmpeg para download/concatenação de vídeos

Tqdm para progress bars no terminal

Markdownify para salvar aulas em texto quando vídeo não está disponível

📦 Estrutura
bash
.
├── main.py                      # Ponto de entrada
├── downloader/                  # Módulos especializados
│   ├── auth.py                  # Gestão de sessão (cookies via Pickle)
│   ├── extract_m3u8.py          # Extração da melhor qualidade de stream
│   ├── video_downloader.py      # Pipeline de download/concatenação
│   └── ...                      # [+4 módulos organizados]
├── downloads/                   # Saída de vídeos e markdowns
└── .config/                     # Dados sensíveis (gitignorados)
🚀 Como Usar
Instale as dependências:

bash
pip install -r requirements.txt
# FFmpeg separadamente (apt/brew/choco)

Execute:

bash
python main.py

No seu primeiro acesso, vai ser solicitado login e senha. esses dados ficam salvos em config.json com credenciais válidas para sessões futuras <nota>você pode melhorar isso com bcrypt se desejar</nota> (só você tem acesso!).

Escolha no menu entre:
▶ Aula única | ▶ Lista de aulas | ▶ Curso completo

🧠 Arquitetura & Lições
Evolução: Começou como script monolítico e foi sendo modularizado conforme a complexidade crescia.

Próximos passos:

Migrar get_course_page para fetcher.py

Decidir se a CLI principal deve ser refatorada

Filosofia: Priorizei ter um MVP funcional rápido, mas mantendo o código adaptável para melhorias incrementais.

⚠️ Aviso Legal
Este projeto não viola DRM — apenas automatiza acesso legítimo via login. Use-o apenas para conteúdo que você tem direito de acessar, e sempre respeite os termos das plataformas. (Responsabilidade é sua.)

📩 Contato
Se você também está reinventando sua carreira através de código, vamos conversar! Me encontre no LinkedIn ou comente no post sobre o projeto.