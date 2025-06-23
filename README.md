# 🖨️ PrintBox - Impressão em Lote de PDFs

O **PrintBox** é uma aplicação Python com interface gráfica que facilita a **impressão em lote de arquivos PDF**, permitindo a criação de grupos de documentos, controle de cópias e um painel de monitoramento com histórico detalhado.

---

## 🚀 Funcionalidades

- 📂 **Organize arquivos em grupos** (pastas separadas)
- 📄 **Imprima PDFs em lote** com múltiplas cópias
- 🔎 **Selecione arquivos individualmente** ou o grupo inteiro para imprimir
- 🔄 **Atualize grupos facilmente**: remova PDFs antigos e adicione novos arquivos
- 🕓 **Histórico de impressões** armazenado com data, hora, nome do arquivo, grupo, páginas e status
- 📊 **Análises gráficas** de impressões por dia
- 🧠 **Interface moderna e leve**, baseada em `ttkthemes`

---

## 📁 Gerenciamento de Arquivos

- Os grupos de arquivos são organizados em uma pasta chamada `grupos_de_arquivos`.
- Cada grupo é uma **pasta com arquivos PDF**.
- Você pode:
  - Selecionar **uma pasta inteira para virar um novo grupo** (nome do grupo = nome da pasta).
  - **Excluir os arquivos antigos** e adicionar novos PDFs dentro da pasta do grupo (diretamente pelo sistema ou usando o botão de upload).
  - O programa recarrega a lista automaticamente sempre que o grupo é alterado.

---

## 📦 Requisitos

- Python 3.8 ou superior
- Dependências (instale com o comando abaixo):

```bash
pip install -r requirements.txt

Ou instale manualmente:

pip install pillow pandas tkcalendar python-docx qrcode ttkthemes PyPDF2 matplotlib

▶️ Como usar

    Clone o repositório:

git clone https://github.com/isarloiola/printbox.git
cd printbox

    Crie um ambiente virtual (recomendado):

python3 -m venv venv
source venv/bin/activate     # Linux/macOS
venv\Scripts\activate        # Windows

    Instale os pacotes:

pip install -r requirements.txt

    Execute o programa:

python printbox.py

💡 Dicas de uso

    Use o botão Upload de Arquivos para adicionar PDFs ao grupo selecionado.

    O nome da pasta selecionada vira o nome do grupo.

    A aba Monitoramento mostra todo o histórico de impressão.

    Clique em "Gerar Gráfico" para ver o uso por data.

📫 Contato

Desenvolvido por Isar Loiola
📧 Email: isarloiola@gmail.com
🔗 GitHub: github.com/isarloiola
🪪 Licença

Este projeto está sob a licença MIT. Sinta-se livre para usar, modificar e compartilhar!


