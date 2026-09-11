import sys
import pandas as pd
import re
import os
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                             QPushButton, QFileDialog, QCheckBox, QHBoxLayout, 
                             QLabel, QLineEdit, QFormLayout, QMessageBox, QColorDialog,
                             QListWidget, QListWidgetItem, QFrame, QSlider, QGroupBox) 
from PyQt5.QtGui import QColor, QIcon, QPixmap
from PyQt5.QtCore import QSize, Qt, QTimer

# Importações do Matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# --- FUNÇÃO ADICIONAL PARA GARANTIR VALORES ZERO NAS EXTREMIDADES ---
def ensure_zero_at_bounds(df):
    if df.empty:
        return df
    min_energy = df['Energy'].min()
    max_energy = df['Energy'].max()
    df_start = pd.DataFrame([{'Energy': min_energy, 'DOS': 0.0, 'Energy_original': df['Energy_original'].min()}])
    df_end = pd.DataFrame([{'Energy': max_energy, 'DOS': 0.0, 'Energy_original': df['Energy_original'].max()}])
    df_new = pd.concat([df_start, df, df_end]).drop_duplicates(subset=['Energy']).sort_values('Energy').reset_index(drop=True)
    return df_new

# --- 1. FUNÇÃO DE PROCESSAMENTO DE DADOS ---
def parse_pdos_file(filepath, fermi_reference=None):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        fermi_from_file = None
        fermi_energy_match = re.search(r'Fermi energy : ([-+]?\d+\.\d+)', content)
        if fermi_energy_match:
            fermi_from_file = float(fermi_energy_match.group(1))
        if fermi_reference is not None:
            fermi_to_use = fermi_reference
            if fermi_from_file is not None and fermi_from_file != fermi_reference:
                print(f"Aviso: Fermi do arquivo ({fermi_from_file}) diferente do Fermi de referência ({fermi_reference}) para {os.path.basename(filepath)}. Usando referência.")
        elif fermi_from_file is not None:
            fermi_to_use = fermi_from_file
        else:
            print(f"Aviso: Nível de Fermi não encontrado e nenhum de referência fornecido para {os.path.basename(filepath)}. Usando 0.0.")
            fermi_to_use = 0.0
        data_lines = [line.strip() for line in content.split('\n') if not line.strip().startswith('#') and len(line.strip().split()) == 2]
        df = pd.read_csv(pd.io.common.StringIO('\n'.join(data_lines)), delim_whitespace=True, header=None, names=['Energy', 'DOS'])
        df['Energy_original'] = df['Energy'].copy() 
        df['Energy'] = df['Energy_original'] - fermi_to_use
        df = ensure_zero_at_bounds(df)
        return df, fermi_to_use
    except Exception as e:
        print(f"Erro ao processar o arquivo {os.path.basename(filepath)}: {e}")
        return None, None
        
def parse_bands_file(filepath):
    try:
        with open(filepath, 'r') as f:
            first_line = f.readline()
        fermi_energy = float(first_line.strip().split()[0])
        return fermi_energy
    except Exception as e:
        print(f"Erro ao ler o nível de Fermi do arquivo {os.path.basename(filepath)}: {e}")
        return None

# --- CLASSE DA JANELA DE CONFIGURAÇÃO DE SUBPLOT ---
class SubplotConfigWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Subplot configuration tool")
        self.setGeometry(200, 200, 500, 450)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        
        layout = QVBoxLayout(self)
        
        self.sliders = {}
        
        params = [
            ('left', 0.0, 0.5, 0.125),
            ('bottom', 0.0, 0.5, 0.11),
            ('right', 0.5, 1.0, 0.9),
            ('top', 0.5, 1.0, 0.88),
            ('wspace', 0.0, 1.0, 0.2),
            ('hspace', 0.0, 1.0, 0.2)
        ]
        
        form_layout = QFormLayout()
        
        for name, min_val, max_val, default_val in params:
            h_layout = QHBoxLayout()
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 1000)
            slider.setValue(int(default_val * 1000))
            
            value_label = QLabel(f"{default_val:.3f}")
            value_label.setFixedWidth(50)
            
            slider.valueChanged.connect(lambda value, n=name, l=value_label: self.update_value(n, value, l))
            
            h_layout.addWidget(slider)
            h_layout.addWidget(value_label)
            
            form_layout.addRow(f"{name}:", h_layout)
            self.sliders[name] = slider

        layout.addLayout(form_layout)
        
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_values)
        layout.addWidget(reset_btn, alignment=Qt.AlignRight)
        
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def update_value(self, name, value, label):
        real_value = value / 1000.0
        label.setText(f"{real_value:.3f}")
        self.main_window.subplot_params[name] = real_value
        self.main_window.update_plot()

    def reset_values(self):
        defaults = {'left': 0.125, 'bottom': 0.11, 'right': 0.9, 'top': 0.88, 'wspace': 0.2, 'hspace': 0.2}
        for name, slider in self.sliders.items():
            slider.setValue(int(defaults[name] * 1000))

# --- CLASSE DA TELA DE INTRODUÇÃO (POP-UP) ---
class SplashScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setFixedSize(700, 700) 
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border: none;
                border-radius: 10px;
                color: #333;
                font-family: "Segoe UI", "Helvetica Neue", "Arial", sans-serif;
            }
            QLabel { border: none; }
            QPushButton {
                background-color: #007bff;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0056b3; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        top_layout = QHBoxLayout()
        gnc_logo = QLabel()
        ufpi_logo = QLabel()
        try:
            gnc_logo.setPixmap(QPixmap('imagens/gnc.png').scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            ufpi_logo.setPixmap(QPixmap('imagens/ufpi.png').scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except FileNotFoundError:
            gnc_logo.setText("GNC Logo Missing")
            ufpi_logo.setText("UFPI Logo Missing")
            gnc_logo.setAlignment(Qt.AlignCenter)
            ufpi_logo.setAlignment(Qt.AlignCenter)
            gnc_logo.setStyleSheet("border: 1px dashed gray;")
            ufpi_logo.setStyleSheet("border: 1px dashed gray;")

        top_layout.addWidget(gnc_logo)
        top_layout.addStretch()
        top_layout.addWidget(ufpi_logo)
        layout.addLayout(top_layout)

        description_text = """
        <h2 style="text-align: center; color: #007bff;">Visualizador de Densidade de Estados</h2>
        <p style="text-align: justify; line-height: 1.5;">Este software foi desenvolvido para auxiliar na análise e visualização de arquivos de Densidade de Estados (PDOS), permitindo o carregamento de múltiplos arquivos, a normalização por um nível de Fermi de referência e a personalização de cores e legendas.</p>
        <p style="text-align: justify; font-size: 13px; line-height: 1.5;">O software foi criado por Henrique Lago, físico formado pela Universidade Federal do Piauí (UFPI), durante sua Iniciação Científica Voluntária, sob orientação do Professor Dr. Ramon Sampaio Ferreira. O desenvolvimento ocorreu no âmbito do Grupo de Nanofísica Computacional (GNC) da UFPI.</p>
        <p style="text-align: center; font-weight: bold;">Conheça mais sobre o grupo escaneando o QR Code abaixo:</p>
        """
        description_label = QLabel(description_text)
        description_label.setWordWrap(True)
        layout.addWidget(description_label)

        qr_layout = QHBoxLayout()
        qr_label = QLabel()
        try:
            qr_label.setPixmap(QPixmap('imagens/qr.png').scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except FileNotFoundError:
            qr_label.setText("QR Code Missing")
            qr_label.setAlignment(Qt.AlignCenter)
            qr_label.setStyleSheet("border: 1px dashed gray;")

        qr_layout.addStretch()
        qr_layout.addWidget(qr_label)
        qr_layout.addStretch()
        layout.addLayout(qr_layout)

        email_label = QLabel("Para colaborações: <a href='mailto:henrique.liberato@ufpi.edu.br' style='color: #007bff; text-decoration: none;'>henrique.liberato@ufpi.edu.br</a>")
        email_label.setAlignment(Qt.AlignCenter)
        email_label.setOpenExternalLinks(True)
        layout.addWidget(email_label)

        button_layout = QHBoxLayout()
        self.tutorial_button = QPushButton("Tutorial")
        self.tutorial_button.clicked.connect(self.show_tutorial)
        self.continue_button = QPushButton("Seguir")
        self.continue_button.clicked.connect(self.close_and_open_main)

        button_layout.addStretch()
        button_layout.addWidget(self.tutorial_button)
        button_layout.addSpacing(20)
        button_layout.addWidget(self.continue_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

    def close_and_open_main(self):
        self.close()
        self.main_window.show()

    def show_tutorial(self):
        tutorial_text = """
        <h3 style="text-align: center;"><b>Guia de Uso do Visualizador de Densidade de Estados</b></h3>
        <p>Este software foi projetado para visualizar arquivos de Densidade de Estados (DOS) e Densidade de Estados Parciais (PDOS).</p>
        <p><b>Para o funcionamento, é necessário:</b></p>
        <ul>
            <li><b>Arquivos PDOS (.dat):</b> Os dados de DOS ou PDOS que serão plotados.</li>
            <li><b>Arquivos de Bandas (.bands):</b> (Opcional) Usado para carregar o Nível de Fermi ($E_F$) para normalizar a energia.</li>
        </ul>
        <p><b>Siga estes passos para plotar seus gráficos:</b></p>
        <ol>
            <li><b>Carregar o Nível de Fermi (Recomendado):</b><br>Clique no botão "Carregar Nível de Fermi (.bands)".</li>
            <li><b>Carregar os Dados de Densidade de Estados:</b><br>Clique em "Carregar Arquivos PDOS".</li>
            <li><b>Personalizar as Curvas:</b><br>Na lista "Curvas Plotadas", clique no nome de uma curva para alterar cor, legenda ou remover.</li>
            <li><b>Ajustar o Gráfico:</b><br>Use as opções em "Personalização do Gráfico" e "Layout e Proporção".</li>
            <li><b>Exportar o Gráfico:</b><br>Use os botões "Exportar Gráfico (PNG)", "(PDF)" ou "(SVG)".</li>
        </ol>
        """
        QMessageBox.information(self, "Tutorial de Uso", tutorial_text)


# --- CLASSE DA INTERFACE GRÁFICA PRINCIPAL ---
class PDOSVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visualizador de PDOS")
        self.setGeometry(100, 100, 1400, 800)
        
        self.loaded_data = {}
        self.fermi_reference = None
        self.selected_filepath = None
        
        self.subplot_params = {
            'left': 0.125, 'right': 0.9, 
            'bottom': 0.11, 'top': 0.88, 
            'wspace': 0.2, 'hspace': 0.2
        }
        self.subplot_window = None
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        left_panel_layout = QVBoxLayout()
        main_layout.addLayout(left_panel_layout, 1)

        load_buttons_layout = QVBoxLayout()
        load_buttons_layout.addWidget(QLabel("Carregamento de Dados"))
        self.load_fermi_button = QPushButton("Carregar Nível de Fermi (.bands)")
        self.load_fermi_button.clicked.connect(self.load_fermi_reference)
        load_buttons_layout.addWidget(self.load_fermi_button)
        self.load_pdos_button = QPushButton("Carregar Arquivos PDOS")
        self.load_pdos_button.clicked.connect(self.load_pdos_files)
        load_buttons_layout.addWidget(self.load_pdos_button)
        left_panel_layout.addLayout(load_buttons_layout)

        left_panel_layout.addWidget(QLabel("Curvas Plotadas"))
        self.pdos_list_widget = QListWidget()
        self.pdos_list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.pdos_list_widget.itemSelectionChanged.connect(self.handle_selection_change)
        left_panel_layout.addWidget(self.pdos_list_widget)

        # Painel de personalização da curva
        self.customization_frame = QFrame()
        self.customization_frame.setFrameShape(QFrame.StyledPanel)
        customization_layout = QFormLayout(self.customization_frame)
        customization_layout.addWidget(QLabel("Personalizar Curva Selecionada"))
        
        self.label_input = QLineEdit()
        self.label_input.editingFinished.connect(self.update_label)
        customization_layout.addRow("Nome da Legenda:", self.label_input)
        
        self.color_button = QPushButton("Alterar Cor")
        self.color_button.clicked.connect(self.select_plot_color)
        customization_layout.addRow("Cor da Curva:", self.color_button)

        self.remove_curve_button = QPushButton("Remover Curva Selecionada")
        self.remove_curve_button.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold;")
        self.remove_curve_button.clicked.connect(self.remove_selected_curve)
        customization_layout.addRow(self.remove_curve_button)

        self.customization_frame.hide()
        left_panel_layout.addWidget(self.customization_frame)
        
        # Painel de configurações gerais
        axis_settings_layout = QFormLayout()
        axis_settings_layout.addWidget(QLabel("Personalização do Gráfico"))
        self.invert_checkbox = QCheckBox("Inverter Eixos (DOS vs Energia)")
        self.invert_checkbox.stateChanged.connect(self.update_plot)
        axis_settings_layout.addWidget(self.invert_checkbox)
        
        self.show_fermi_checkbox = QCheckBox("Mostrar Nível de Fermi")
        self.show_fermi_checkbox.setChecked(True)
        self.show_fermi_checkbox.stateChanged.connect(self.update_plot)
        axis_settings_layout.addWidget(self.show_fermi_checkbox)

        self.show_fermi_legend_checkbox = QCheckBox("Mostrar Legenda Nível de Fermi")
        self.show_fermi_legend_checkbox.setChecked(True)
        self.show_fermi_legend_checkbox.stateChanged.connect(self.update_plot)
        axis_settings_layout.addWidget(self.show_fermi_legend_checkbox)

        self.xaxis_title_input = QLineEdit()
        self.xaxis_title_input.setPlaceholderText("Energia (eV)")
        self.xaxis_title_input.editingFinished.connect(self.update_plot)
        axis_settings_layout.addRow("Título Eixo X:", self.xaxis_title_input)

        self.yaxis_title_input = QLineEdit()
        self.yaxis_title_input.setPlaceholderText("DOS (un. arb.)")
        self.yaxis_title_input.editingFinished.connect(self.update_plot)
        axis_settings_layout.addRow("Título Eixo Y:", self.yaxis_title_input)

        self.font_size_input = QLineEdit()
        self.font_size_input.setPlaceholderText("12")
        self.font_size_input.editingFinished.connect(self.update_plot)
        axis_settings_layout.addRow("Tam. Fonte Eixos:", self.font_size_input)

        self.energy_min_input = QLineEdit()
        self.energy_min_input.setPlaceholderText("Auto")
        self.energy_min_input.editingFinished.connect(self.update_plot)
        axis_settings_layout.addRow("Eixo Energia Min:", self.energy_min_input)
        self.energy_max_input = QLineEdit()
        self.energy_max_input.setPlaceholderText("Auto")
        self.energy_max_input.editingFinished.connect(self.update_plot)
        axis_settings_layout.addRow("Eixo Energia Max:", self.energy_max_input)
        self.dos_min_input = QLineEdit()
        self.dos_min_input.setPlaceholderText("Auto")
        self.dos_min_input.editingFinished.connect(self.update_plot)
        axis_settings_layout.addRow("Eixo DOS Min:", self.dos_min_input)
        self.dos_max_input = QLineEdit()
        self.dos_max_input.setPlaceholderText("Auto")
        self.dos_max_input.editingFinished.connect(self.update_plot)
        axis_settings_layout.addRow("Eixo DOS Max:", self.dos_max_input)
        self.xtick_spacing_input = QLineEdit()
        self.xtick_spacing_input.setPlaceholderText("Auto")
        self.xtick_spacing_input.editingFinished.connect(self.update_plot)
        axis_settings_layout.addRow("Espaçamento Eixo X:", self.xtick_spacing_input)
        self.ytick_spacing_input = QLineEdit()
        self.ytick_spacing_input.setPlaceholderText("Auto")
        self.ytick_spacing_input.editingFinished.connect(self.update_plot)
        axis_settings_layout.addRow("Espaçamento Eixo Y:", self.ytick_spacing_input)
        left_panel_layout.addLayout(axis_settings_layout)

        # Controles de Layout e Proporção
        layout_group = QGroupBox("Layout e Proporção (Estilo Nature)")
        layout_form = QFormLayout()
        
        self.aspect_input = QLineEdit()
        self.aspect_input.setPlaceholderText("Auto (ex: 0.5 para achatado)")
        self.aspect_input.editingFinished.connect(self.update_plot)
        layout_form.addRow("Proporção (Aspect):", self.aspect_input)
        
        self.config_subplot_btn = QPushButton("Ajustar Margens (Subplot Tool)")
        self.config_subplot_btn.clicked.connect(self.open_subplot_config)
        layout_form.addRow(self.config_subplot_btn)
        
        layout_group.setLayout(layout_form)
        left_panel_layout.addWidget(layout_group)

        # --- SEÇÃO DE EXPORTAÇÃO (COM SVG) ---
        export_buttons_layout = QVBoxLayout()
        export_buttons_layout.addWidget(QLabel("Exportar Gráfico"))
        
        self.export_png_button = QPushButton("Exportar Gráfico (PNG)")
        self.export_png_button.clicked.connect(lambda: self.export_plot('png'))
        export_buttons_layout.addWidget(self.export_png_button)
        
        self.export_pdf_button = QPushButton("Exportar Gráfico (PDF)")
        self.export_pdf_button.clicked.connect(lambda: self.export_plot('pdf'))
        export_buttons_layout.addWidget(self.export_pdf_button)
        
        # NOVO: Botão de exportação SVG
        self.export_svg_button = QPushButton("Exportar Gráfico (SVG)")
        self.export_svg_button.clicked.connect(lambda: self.export_plot('svg'))
        export_buttons_layout.addWidget(self.export_svg_button)
        
        left_panel_layout.addLayout(export_buttons_layout)
        left_panel_layout.addStretch()

        right_panel_layout = QVBoxLayout()
        main_layout.addLayout(right_panel_layout, 3)
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        right_panel_layout.addWidget(self.canvas)
        
        self.update_plot()

    def open_subplot_config(self):
        if self.subplot_window is None:
            self.subplot_window = SubplotConfigWindow(self)
        self.subplot_window.show()
        self.subplot_window.raise_()

    def handle_selection_change(self):
        selected_items = self.pdos_list_widget.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            self.selected_filepath = selected_item.data(Qt.UserRole)
            self.customization_frame.show()
            self.update_customization_panel()
        else:
            self.selected_filepath = None
            self.customization_frame.hide()

    def update_customization_panel(self):
        if self.selected_filepath and self.selected_filepath in self.loaded_data:
            data = self.loaded_data[self.selected_filepath]
            self.label_input.setText(data['label'])
            color_name = data['color'] if data['color'] else "black"
            self.color_button.setStyleSheet(f"background-color: {color_name};")
    
    def update_label(self):
        if self.selected_filepath and self.selected_filepath in self.loaded_data:
            new_label = self.label_input.text()
            self.loaded_data[self.selected_filepath]['label'] = new_label
            for i in range(self.pdos_list_widget.count()):
                item = self.pdos_list_widget.item(i)
                if item.data(Qt.UserRole) == self.selected_filepath:
                    item.setText(new_label)
                    break
            self.update_plot()

    def remove_selected_curve(self):
        if self.selected_filepath:
            if self.selected_filepath in self.loaded_data:
                del self.loaded_data[self.selected_filepath]
            
            for i in range(self.pdos_list_widget.count()):
                item = self.pdos_list_widget.item(i)
                if item.data(Qt.UserRole) == self.selected_filepath:
                    self.pdos_list_widget.takeItem(i)
                    break
            
            self.selected_filepath = None
            self.customization_frame.hide()
            self.update_plot()
        else:
            QMessageBox.warning(self, "Erro", "Nenhuma curva selecionada para remover.")

    def select_plot_color(self):
        if self.selected_filepath and self.selected_filepath in self.loaded_data:
            initial_color_name = self.loaded_data[self.selected_filepath]['color']
            initial_color = QColor(initial_color_name) if initial_color_name else QColor("blue")
            color = QColorDialog.getColor(initial_color, self, "Selecione a nova cor para a curva")
            if color.isValid():
                new_color_name = color.name()
                self.loaded_data[self.selected_filepath]['color'] = new_color_name
                self.color_button.setStyleSheet(f"background-color: {new_color_name};")
                self.update_plot()
        else:
            QMessageBox.warning(self, "Erro", "Nenhum arquivo selecionado.")
            
    def load_fermi_reference(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo .bands", "", "Arquivos de Bandas (*.bands)")
        if file_path:
            fermi_value = parse_bands_file(file_path)
            if fermi_value is not None:
                self.fermi_reference = fermi_value
                print(f"Nível de Fermi de referência carregado: {self.fermi_reference} eV")
                if self.loaded_data:
                    self.apply_fermi_to_loaded_data()
                self.update_plot()

    def apply_fermi_to_loaded_data(self):
        if self.fermi_reference is not None:
            for path, data_dict in self.loaded_data.items():
                data_df = data_dict['df']
                if 'Energy_original' not in data_df.columns:
                     data_df['Energy_original'] = data_df['Energy']
                data_df['Energy'] = data_df['Energy_original'] - self.fermi_reference
            print("Nível de Fermi de referência aplicado aos dados carregados.")
        else:
            print("Nenhum nível de Fermi de referência para aplicar.")

    def load_pdos_files(self): 
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Selecionar arquivos PDOS", "", "Arquivos PDOS (*.dat)")
        if file_paths:
            for path in file_paths:
                if path in self.loaded_data:
                    QMessageBox.information(self, "Arquivo Já Carregado", f"O arquivo {os.path.basename(path)} já está carregado e plotado.")
                    continue
                df, _ = parse_pdos_file(path, fermi_reference=self.fermi_reference)
                if df is not None:
                    label = os.path.basename(path).replace('.dat', '')
                    random_color = "#%06x" % random.randint(0, 0xFFFFFF)
                    self.loaded_data[path] = {'df': df, 'color': random_color, 'label': label} 
                    list_item = QListWidgetItem(label)
                    list_item.setData(Qt.UserRole, path)
                    self.pdos_list_widget.addItem(list_item)
            self.update_plot()

    def update_plot(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if not self.loaded_data:
            ax.text(0.5, 0.5, 'Nenhum dado carregado. Por favor, carregue um arquivo.', ha='center', va='center', transform=ax.transAxes)
            self.canvas.draw()
            return
        inverted = self.invert_checkbox.isChecked()
        show_fermi = self.show_fermi_checkbox.isChecked()
        show_fermi_legend = self.show_fermi_legend_checkbox.isChecked()

        for path, data_dict in self.loaded_data.items():
            data = data_dict['df']
            color = data_dict['color']
            label = data_dict['label']
            
            if inverted:
                ax.plot(data['DOS'], data['Energy'], label=label, color=color)
            else:
                ax.plot(data['Energy'], data['DOS'], label=label, color=color)

        x_label_text = self.xaxis_title_input.text().strip()
        y_label_text = self.yaxis_title_input.text().strip()
        
        default_x = 'Energia (eV)' if not inverted else 'DOS (unidades arbitrárias)'
        default_y = 'DOS (unidades arbitrárias)' if not inverted else 'Energia (eV)'
        
        final_x_label = x_label_text if x_label_text else default_x
        final_y_label = y_label_text if y_label_text else default_y

        if x_label_text == " ":
            final_x_label = ""
        if y_label_text == " ":
            final_y_label = ""

        ax.set_xlabel(final_x_label)
        ax.set_ylabel(final_y_label)

        font_size_text = self.font_size_input.text().strip()
        if font_size_text:
            try:
                font_size = float(font_size_text)
                ax.xaxis.label.set_size(font_size)
                ax.yaxis.label.set_size(font_size)
                ax.tick_params(axis='both', which='major', labelsize=font_size-2)
            except ValueError:
                pass

        if inverted:
            if show_fermi:
                if show_fermi_legend:
                    ax.axhline(0, color='gray', linestyle='--', label='Nível de Fermi ($E_F$)')
                else:
                    ax.axhline(0, color='gray', linestyle='--')
            
            try:
                if self.dos_min_input.text() or self.dos_max_input.text():
                    dos_min = float(self.dos_min_input.text()) if self.dos_min_input.text() else None
                    dos_max = float(self.dos_max_input.text()) if self.dos_max_input.text() else None
                    ax.set_xlim(dos_min, dos_max)
                if self.energy_min_input.text() or self.energy_max_input.text():
                    energy_min = float(self.energy_min_input.text()) if self.energy_min_input.text() else None
                    energy_max = float(self.energy_max_input.text()) if self.energy_max_input.text() else None
                    ax.set_ylim(energy_min, energy_max)
                if self.xtick_spacing_input.text():
                    ax.xaxis.set_major_locator(ticker.MultipleLocator(float(self.xtick_spacing_input.text())))
                if self.ytick_spacing_input.text():
                    ax.yaxis.set_major_locator(ticker.MultipleLocator(float(self.ytick_spacing_input.text())))
            except ValueError:
                QMessageBox.warning(self, "Erro de Entrada", "Por favor, insira números válidos para os limites ou espaçamento dos eixos.")
        else:
            if show_fermi:
                if show_fermi_legend:
                    ax.axvline(0, color='gray', linestyle='--', label='Nível de Fermi ($E_F$)')
                else:
                    ax.axvline(0, color='gray', linestyle='--')
            
            try:
                if self.energy_min_input.text() or self.energy_max_input.text():
                    energy_min = float(self.energy_min_input.text()) if self.energy_min_input.text() else None
                    energy_max = float(self.energy_max_input.text()) if self.energy_max_input.text() else None
                    ax.set_xlim(energy_min, energy_max)
                if self.dos_min_input.text() or self.dos_max_input.text():
                    dos_min = float(self.dos_min_input.text()) if self.dos_min_input.text() else None
                    dos_max = float(self.dos_max_input.text()) if self.dos_max_input.text() else None
                    ax.set_ylim(dos_min, dos_max)
                if self.xtick_spacing_input.text():
                    ax.xaxis.set_major_locator(ticker.MultipleLocator(float(self.xtick_spacing_input.text())))
                if self.ytick_spacing_input.text():
                    ax.yaxis.set_major_locator(ticker.MultipleLocator(float(self.ytick_spacing_input.text())))
            except ValueError:
                QMessageBox.warning(self, "Erro de Entrada", "Por favor, insira números válidos para os limites ou espaçamento dos eixos.")
        
        ax.set_title("Densidade de Estados (DOS)")
        ax.legend()
        ax.grid(True, linestyle=':', alpha=0.6)
        
        aspect_text = self.aspect_input.text().strip()
        if aspect_text:
            try:
                aspect_val = float(aspect_text)
                ax.set_aspect(aspect_val)
            except ValueError:
                pass
        else:
            ax.set_aspect('auto')

        self.figure.subplots_adjust(
            left=self.subplot_params['left'],
            right=self.subplot_params['right'],
            bottom=self.subplot_params['bottom'],
            top=self.subplot_params['top'],
            wspace=self.subplot_params['wspace'],
            hspace=self.subplot_params['hspace']
        )
        
        self.canvas.draw()
        
    def export_plot(self, format):
        if not self.loaded_data:
            QMessageBox.warning(self, "Exportar Gráfico", "Nenhum dado para exportar.")
            return
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, f"Salvar Gráfico como .{format}", "", 
                                                   f"Arquivos {format.upper()} (*.{format});;Todos os Arquivos (*)", options=options)
        if file_name:
            try:
                # O parâmetro bbox_inches='tight' remove o excesso de espaço em branco
                # O dpi=300 é ignorado para SVG (vetorial), mas mantido para PNG/PDF
                self.figure.savefig(file_name, format=format, bbox_inches='tight', dpi=300)
                QMessageBox.information(self, "Exportação Sucesso", f"Gráfico salvo como '{file_name}'")
            except Exception as e:
                QMessageBox.critical(self, "Erro de Exportação", f"Não foi possível salvar o gráfico: {e}")

# --- BLOCO PRINCIPAL DE EXECUÇÃO ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = PDOSVisualizer()
    splash = SplashScreen(main_window)
    splash.show()
    sys.exit(app.exec_())
