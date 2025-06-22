# --------------------------------------------------------------------------------
# PrintBox v2.0 - Programa Completo e Refatorado
#
# DESCRIÇÃO:
# Esta versão inclui:
# - Interface gráfica modernizada com temas.
# - Lógica de impressão assíncrona (não trava a interface).
# - Banco de dados SQLite para registrar todos os trabalhos de impressão.
# - Aba de Monitoramento para visualizar o histórico de impressões.
# - Ferramenta de análise para gerar gráficos de uso.
# - Código mais organizado, comentado e com tratamento de erros aprimorado.
#
# PRÉ-REQUISITOS:
# pip install ttkthemes PyPDF2 pandas matplotlib
# --------------------------------------------------------------------------------
import os
import shutil
import subprocess
import sys
import threading
import sqlite3
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import List, Optional

# Libs de terceiros
from PIL import ImageTk, Image
import qrcode
from ttkthemes import ThemedTk
from PyPDF2 import PdfReader


# --- MÓDULO DE BANCO DE DADOS (Poderia ser um arquivo separado: database.py) ---

DB_FILE = "print_log.db"
GRUPOS_DIR = "grupos_de_arquivos"

def setup_database():
    """Cria o arquivo de banco de dados e a tabela de logs se não existirem."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS print_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                filename TEXT NOT NULL,
                group_name TEXT NOT NULL,
                copies INTEGER NOT NULL,
                status TEXT NOT NULL,
                pages INTEGER
            )
        ''')
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        messagebox.showerror("Erro de Banco de Dados", f"Não foi possível inicializar o banco de dados: {e}")
        sys.exit(1)

def log_print_job(filename: str, group: str, copies: int, status: str, pages: Optional[int]):
    """Registra um trabalho de impressão no banco de dados."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO print_jobs (timestamp, filename, group_name, copies, status, pages)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (timestamp, filename, group, copies, status, pages))
    conn.commit()
    conn.close()

def get_all_jobs() -> List[tuple]:
    """Busca todos os trabalhos de impressão do banco de dados, ordenados por data."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, filename, group_name, copies, pages, status FROM print_jobs ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- CLASSE PRINCIPAL DA APLICAÇÃO ---

class PDFPrinterApp:
    """
    Aplicação com interface gráfica para gerenciar e imprimir
    grupos de arquivos PDF, com monitoramento e análise.
    """
    def __init__(self, root: ThemedTk):
        self.root = root
        self._setup_main_window()
        self._setup_variables()
        self._criar_diretorio_grupos()

        self.grupos = self.carregar_grupos()
        self._setup_ui()
        

    def _setup_main_window(self):
        """Configura a janela principal."""
        self.root.title("PrintBox v2.0 - Gerenciador de Impressão")
        self.root.geometry("1000x700")
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

    def _setup_variables(self):
        """Inicializa as variáveis de controle do Tkinter."""
        self.grupo_var = tk.StringVar()
        self.num_copias_var = tk.IntVar(value=1)
        self.check_vars = {}
        self.is_printing = threading.Event() # Para controlar se uma impressão está em andamento

    def _setup_ui(self):
        """Constrói a interface gráfica do usuário."""
        # --- Painel Esquerdo com Abas ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.print_tab = ttk.Frame(self.notebook, padding="10")
        self.monitor_tab = ttk.Frame(self.notebook, padding="10")

        self.notebook.add(self.print_tab, text='🖨️ Impressão')
        self.notebook.add(self.monitor_tab, text='📊 Monitoramento')

        self._setup_printing_tab()
        self._setup_monitoring_tab()

        # --- Painel Direito de Informações ---
        self._setup_info_panel()

    def _setup_printing_tab(self):
        """Configura a aba de impressão."""
        # Frame de seleção de grupo e impressão geral
        group_frame = ttk.LabelFrame(self.print_tab, text="1. Seleção de Grupo", padding="10")
        group_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        group_frame.columnconfigure(0, weight=1)

        self.grupo_dropdown = ttk.Combobox(group_frame, textvariable=self.grupo_var, values=self.grupos, state="readonly")
        self.grupo_dropdown.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.grupo_dropdown.set("Selecione um grupo")
        self.grupo_dropdown.bind("<<ComboboxSelected>>", self.carregar_pdfs)

        self.imprimir_grupo_button = ttk.Button(group_frame, text="Imprimir Grupo Inteiro", command=self.imprimir_grupo)
        self.imprimir_grupo_button.grid(row=0, column=1, padx=5, pady=5)

        # Frame de arquivos e opções
        files_frame = ttk.LabelFrame(self.print_tab, text="2. Seleção de Arquivos e Opções", padding="10")
        files_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=10)
        self.print_tab.rowconfigure(1, weight=1)

        self.checkbox_frame = ttk.Frame(files_frame)
        self.checkbox_frame.pack(expand=True, fill='both')

        options_frame = ttk.Frame(self.print_tab)
        options_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        options_frame.columnconfigure(1, weight=1)

        ttk.Label(options_frame, text="Número de cópias:").grid(row=0, column=0, padx=5)
        self.num_copias_entry = ttk.Entry(options_frame, textvariable=self.num_copias_var, width=5)
        self.num_copias_entry.grid(row=0, column=1, padx=5, sticky="w")

        self.print_button = ttk.Button(options_frame, text="Imprimir Selecionados", command=self.imprimir_selecionados)
        self.print_button.grid(row=0, column=2, padx=5, sticky="e")
        options_frame.columnconfigure(2, weight=1)
        
        # Frame de status
        status_frame = ttk.LabelFrame(self.print_tab, text="Status da Impressão", padding="10")
        status_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)

        self.progress_bar = ttk.Progressbar(status_frame, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill="x", expand=True, pady=5)
        self.status_label = ttk.Label(status_frame, text="Aguardando uma tarefa...")
        self.status_label.pack(fill="x", expand=True)

    def _setup_monitoring_tab(self):
        """Configura a aba de monitoramento."""
        self.monitor_tab.columnconfigure(0, weight=1)
        self.monitor_tab.rowconfigure(0, weight=1)
        
        cols = ('Data/Hora', 'Arquivo', 'Grupo', 'Cópias', 'Páginas', 'Status')
        self.jobs_treeview = ttk.Treeview(self.monitor_tab, columns=cols, show='headings')

        for col in cols:
            self.jobs_treeview.heading(col, text=col)
        self.jobs_treeview.column('Data/Hora', width=150, anchor='center')
        self.jobs_treeview.column('Arquivo', width=200)
        self.jobs_treeview.column('Grupo', width=100)
        self.jobs_treeview.column('Cópias', width=60, anchor='center')
        self.jobs_treeview.column('Páginas', width=60, anchor='center')
        self.jobs_treeview.column('Status', width=80, anchor='center')
        
        self.jobs_treeview.grid(row=0, column=0, sticky="nsew")

        # Scrollbar para a Treeview
        scrollbar = ttk.Scrollbar(self.monitor_tab, orient="vertical", command=self.jobs_treeview.yview)
        self.jobs_treeview.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Botões de Ação
        action_frame = ttk.Frame(self.monitor_tab)
        action_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky="e")
        
        ttk.Button(action_frame, text="Gerar Gráfico de Análise", command=self.show_prints_per_day_chart).pack(side='left', padx=5)
        ttk.Button(action_frame, text="Atualizar Dados", command=self.refresh_monitoring_data).pack(side='left', padx=5)

        self.refresh_monitoring_data()


    def _setup_info_panel(self):
        """Configura o painel lateral de informações."""
        self.info_frame = ttk.LabelFrame(self.root, text="Sobre", padding="10")
        self.info_frame.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=10)

        ttk.Label(self.info_frame, text="PrintBox", font=("Arial", 16, "bold")).pack(pady=5)
        ttk.Label(self.info_frame, text="Versão: 2.0", font=("Arial", 10)).pack(pady=5)
        
        ttk.Separator(self.info_frame, orient="horizontal").pack(fill='x', pady=10)

        # Botão de Upload
        ttk.Button(self.info_frame, text="Upload de Arquivos", command=self.upload_arquivos).pack(pady=10, fill='x')

        ttk.Separator(self.info_frame, orient="horizontal").pack(fill='x', pady=10)

        # Doações
        donation_frame = ttk.Frame(self.info_frame)
        donation_frame.pack(pady=5)
        ttk.Label(donation_frame, text="Apoie o projeto:", font=("Arial", 10)).pack()
        ttk.Label(donation_frame, text="Chave PIX: isarloiola@gmail.com", font=("Arial", 9, "italic")).pack()
        
        try:
            self.qr_code_image = self.criar_qr_code("00020101021126580014br.gov.bcb.pix0136e99fe61e-c0d7-4b28-8449-3b10bf07c8515204000053039865802BR5917ISAR BAERE LOIOLA6013RIO DE JANEIR62070503***6304D833", 150)
            ttk.Label(donation_frame, image=self.qr_code_image).pack(pady=10)
        except Exception as e:
            ttk.Label(donation_frame, text=f"Erro ao gerar QR Code: {e}").pack()
        
        ttk.Button(self.info_frame, text="Ajuda", command=self.exibir_ajuda).pack(pady=10, fill='x')

        # Footer
        footer_frame = ttk.Frame(self.info_frame)
        footer_frame.pack(side='bottom', pady=10)
        ttk.Label(footer_frame, text="© 2024 PrintBox", font=("Arial", 8)).pack()

    def _criar_diretorio_grupos(self):
        """Cria a pasta para armazenar os grupos de arquivos se não existir."""
        if not os.path.exists(GRUPOS_DIR):
            try:
                os.makedirs(GRUPOS_DIR)
            except OSError as e:
                messagebox.showerror("Erro Crítico", f"Erro ao criar diretório de grupos: {e}")
                sys.exit(1)

    def carregar_grupos(self) -> List[str]:
        """Carrega os grupos de arquivos (pastas)."""
        try:
            return [nome for nome in os.listdir(GRUPOS_DIR) if os.path.isdir(os.path.join(GRUPOS_DIR, nome))]
        except OSError as e:
            messagebox.showerror("Erro", f"Erro ao carregar grupos: {e}")
            return []

    def carregar_pdfs(self, event=None):
        """Carrega os arquivos PDF de um grupo selecionado."""
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()

        grupo_selecionado = self.grupo_var.get()
        if not grupo_selecionado or grupo_selecionado == "Selecione um grupo":
            return

        grupo_path = os.path.join(GRUPOS_DIR, grupo_selecionado)
        try:
            pdf_files = [f for f in os.listdir(grupo_path) if f.lower().endswith(".pdf")]
        except OSError as e:
            messagebox.showerror("Erro", f"Erro ao listar arquivos PDF: {e}")
            return

        self.check_vars = {}
        for idx, file in enumerate(sorted(pdf_files)):
            var = tk.BooleanVar()
            self.check_vars[file] = var
            chk = ttk.Checkbutton(self.checkbox_frame, text=file, variable=var)
            chk.pack(anchor='w', padx=5)

    def _get_pdf_page_count(self, file_path: str) -> Optional[int]:
        """Retorna o número de páginas de um arquivo PDF."""
        try:
            with open(file_path, 'rb') as f:
                reader = PdfReader(f, strict=False)
                return len(reader.pages)
        except Exception:
            return None

    def _iniciar_processo_impressao(self, arquivos_para_imprimir: List[str]):
        """Valida e inicia a thread de impressão."""
        if self.is_printing.is_set():
            messagebox.showwarning("Atenção", "Um processo de impressão já está em andamento. Aguarde.")
            return

        grupo_selecionado = self.grupo_var.get()
        if not grupo_selecionado or grupo_selecionado == "Selecione um grupo":
            messagebox.showwarning("Atenção", "Selecione um grupo de arquivos primeiro.")
            return

        if not arquivos_para_imprimir:
            messagebox.showwarning("Atenção", "Nenhum arquivo para imprimir.")
            return
            
        try:
            num_copias = self.num_copias_var.get()
            if num_copias < 1:
                messagebox.showerror("Erro", "O número de cópias deve ser pelo menos 1.")
                return
        except tk.TclError:
            messagebox.showerror("Erro", "Número de cópias inválido.")
            return

        # Inicia a impressão em uma nova thread para não travar a GUI
        print_thread = threading.Thread(
            target=self._processar_impressao_thread,
            args=(arquivos_para_imprimir, num_copias, grupo_selecionado)
        )
        print_thread.start()

    def imprimir_grupo(self):
        """Prepara todos os arquivos do grupo para impressão."""
        grupo_selecionado = self.grupo_var.get()
        grupo_path = os.path.join(GRUPOS_DIR, grupo_selecionado)
        try:
            pdf_files = [f for f in os.listdir(grupo_path) if f.lower().endswith(".pdf")]
            self._iniciar_processo_impressao(pdf_files)
        except OSError as e:
            messagebox.showerror("Erro", f"Não foi possível ler os arquivos do grupo: {e}")

    def imprimir_selecionados(self):
        """Prepara os arquivos selecionados para impressão."""
        selected_files = [file for file, var in self.check_vars.items() if var.get()]
        self._iniciar_processo_impressao(selected_files)

    def _processar_impressao_thread(self, files_to_print: List[str], num_copias: int, grupo: str):
        """
        Executa a impressão em uma thread separada para não bloquear a interface.
        """
        self.is_printing.set()
        total_files = len(files_to_print)
        grupo_path = os.path.join(GRUPOS_DIR, grupo)

        for idx, filename in enumerate(files_to_print):
            progress = (idx + 1) / total_files * 100
            self.root.after(0, self.progress_bar.config, {'value': progress})
            self.root.after(0, self.status_label.config, {'text': f'Imprimindo {idx+1}/{total_files}: {filename}'})
            
            full_path = os.path.join(grupo_path, filename)
            pages = self._get_pdf_page_count(full_path)
            
            status = "Sucesso"
            try:
                for _ in range(num_copias):
                    self._print_pdf_subprocess(full_path)
            except Exception as e:
                status = "Falha"
                self.root.after(0, messagebox.showerror, "Erro de Impressão", f"Falha ao imprimir {filename}: {e}")

            log_print_job(filename, grupo, num_copias, status, pages)

        # Tarefa concluída
        self.root.after(0, self.status_label.config, {'text': f'Impressão de {total_files} arquivo(s) concluída!'})
        self.root.after(0, self.progress_bar.config, {'value': 0})
        self.root.after(0, messagebox.showinfo, "Concluído", "Todos os arquivos foram enviados para a fila de impressão.")
        self.root.after(0, self.refresh_monitoring_data) # Atualiza a aba de monitoramento
        self.is_printing.clear()

    def _print_pdf_subprocess(self, file_path: str):
        """Chama o comando do sistema para imprimir o PDF."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"O arquivo {file_path} não foi encontrado.")
            
        try:
            if sys.platform == "win32":
                # Tenta usar o comando 'print' que é mais universal no Windows moderno
                # Se falhar, pode-se adicionar um fallback para 'start acrord32.exe /p /h'
                os.startfile(file_path, "print")
            elif sys.platform == "darwin": # macOS
                subprocess.run(["lpr", file_path], check=True)
            else: # Linux e outros
                subprocess.run(["lp", file_path], check=True)
        except Exception as e:
            raise OSError(f"Comando de impressão falhou: {e}")

    def upload_arquivos(self):
        """Permite criar um novo grupo com arquivos PDF, via seleção de arquivos ou pasta."""
        arquivos = []
        usar_pasta = messagebox.askyesno(
            "Upload",
            "Você quer importar uma PASTA?\n\nSim = Escolher pasta\nNão = Selecionar arquivos PDF"
        )   

        if usar_pasta:
            # Seleção de pasta
            pasta = filedialog.askdirectory(title="Selecione a pasta com arquivos PDF")
            if not pasta:
                return
            nome_grupo = os.path.basename(pasta)
            arquivos = [os.path.join(pasta, f) for f in os.listdir(pasta) if f.lower().endswith(".pdf")]
        else:
            # Seleção de arquivos
            arquivos = filedialog.askopenfilenames(
                title="Selecione arquivos PDF",
                filetypes=[("Arquivos PDF", "*.pdf")]
            )
            if not arquivos:
                return
            nome_grupo = simpledialog.askstring("Novo Grupo", "Digite um nome para o novo grupo:")
            if not nome_grupo:
                return

        grupo_path = os.path.join(GRUPOS_DIR, nome_grupo)

        if os.path.exists(grupo_path):
            messagebox.showerror("Erro", f"O grupo '{nome_grupo}' já existe.")
            return

        try:
            os.makedirs(grupo_path)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao criar o grupo: {e}")
            return

        copiados = 0
        for arquivo in arquivos:
            try:
                shutil.copy(arquivo, grupo_path)
                copiados += 1
            except Exception as e:
                messagebox.showwarning("Erro", f"Erro ao copiar {os.path.basename(arquivo)}: {e}")

        # Atualiza os grupos disponíveis
        self.grupos = self.carregar_grupos()
        self.grupo_dropdown['values'] = self.grupos
        self.grupo_dropdown.set(nome_grupo)
        self.carregar_pdfs()

        messagebox.showinfo("Sucesso", f"{copiados} arquivo(s) foram adicionados ao grupo '{nome_grupo}'.")

    def exibir_ajuda(self):
        """Exibe uma caixa de diálogo com informações de ajuda."""
        messagebox.showinfo("Ajuda - PrintBox",
            "1. **Selecione um Grupo:** Use o menu para escolher uma pasta de trabalho.\n\n"
            "2. **Selecione Arquivos:** Marque os PDFs que deseja imprimir na lista.\n\n"
            "3. **Defina Cópias:** Insira o número de cópias desejado.\n\n"
            "4. **Imprima:**\n"
            "   - 'Imprimir Grupo Inteiro': Envia todos os PDFs do grupo para a impressora.\n"
            "   - 'Imprimir Selecionados': Envia apenas os arquivos marcados.\n\n"
            "5. **Upload:** Use o botão no painel direito para adicionar novos PDFs ao grupo selecionado.\n\n"
            "6. **Monitoramento:** A aba 'Monitoramento' mostra um histórico de todas as impressões e permite gerar análises gráficas."
        )

    def criar_qr_code(self, dados: str, size: int) -> ImageTk.PhotoImage:
        """Cria uma imagem de QR Code."""
        img = qrcode.make(dados)
        img = img.resize((size, size))
        return ImageTk.PhotoImage(img)

    def refresh_monitoring_data(self):
        """Limpa e recarrega os dados na Treeview de monitoramento."""
        for i in self.jobs_treeview.get_children():
            self.jobs_treeview.delete(i)

        jobs = get_all_jobs()
        for job in jobs:
            timestamp_str = datetime.datetime.fromisoformat(job[0]).strftime('%d/%m/%Y %H:%M:%S')
            data = (timestamp_str,) + job[1:]
            self.jobs_treeview.insert("", "end", values=data)

    def show_prints_per_day_chart(self):
        # --- IMPORTS ATRASADOS ---
        # Importa as bibliotecas pesadas somente quando esta função é chamada
        import pandas as pd
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        # -------------------------
        
        """Busca dados e gera um gráfico de impressões por dia."""
        jobs = get_all_jobs()
        if not jobs:
            messagebox.showinfo("Análise de Dados", "Não há dados suficientes para gerar um gráfico.")
            return

        df = pd.DataFrame(jobs, columns=['timestamp', 'filename', 'group', 'copies', 'pages', 'status'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        # Agrupa por data e conta o número de trabalhos (linhas)
        prints_per_day = df.groupby('date').size()

        # Cria uma nova janela para o gráfico
        chart_window = tk.Toplevel(self.root)
        chart_window.title("Análise: Impressões por Dia")
        chart_window.geometry("600x450")

        fig, ax = plt.subplots(figsize=(8, 5))
        prints_per_day.plot(kind='bar', ax=ax, color='skyblue')
        ax.set_title('Total de Trabalhos de Impressão por Dia', fontsize=14)
        ax.set_ylabel("Número de Impressões")
        ax.set_xlabel("Data")
        ax.tick_params(axis='x', rotation=45)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chart_window)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True, fill='both', padx=10, pady=10)


# --- PONTO DE ENTRADA DA APLICAÇÃO ---
if __name__ == "__main__":
    # Garante que o banco de dados está pronto
    setup_database()

    # Cria a janela principal usando um tema moderno
    # Temas bons: "arc", "plastik", "radiance", "clam", "alt"
    root = ThemedTk(theme="arc")
    
    app = PDFPrinterApp(root)
    root.mainloop()