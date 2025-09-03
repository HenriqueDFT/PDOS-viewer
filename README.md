# Visualizador de Densidade de Estados (DOS-viewer)

## 💻 Sobre o Projeto

O **DOS-viewer** é um software de desktop desenvolvido em Python com **PyQt5** e **Matplotlib** para facilitar a visualização e análise de arquivos de Densidade de Estados (DOS) e Densidade de Estados Parciais (PDOS).

O software permite:
- **Carregamento de Múltiplos Arquivos:** Visualize várias curvas PDOS no mesmo gráfico.
- **Normalização de Energia:** Normalize as energias em relação a um Nível de Fermi de referência carregado de arquivos de bandas (`.bands`).
- **Personalização de Gráficos:** Altere rótulos, cores e os limites dos eixos do gráfico.
- **Exportação de Imagens:** Salve gráficos em formatos de alta qualidade como PNG e PDF.

Este projeto foi desenvolvido por Henrique Lago como parte de sua Iniciação Científica Voluntária no **Grupo de Nanofísica Computacional (GNC)** da Universidade Federal do Piauí (UFPI).

---

## 🚀 Como Executar

### Pré-requisitos
Certifique-se de ter o Python 3.x instalado.

### ⚙️ Instalação

Clone este repositório para a sua máquina local:

```bash
git clone https://github.com/seu-usuario/DOS-viewer.git

```
Navegue até o diretório do projeto:

```bash
cd DOS-viewer
```
Instale as dependências necessárias usando o pip:

```bash
pip install -r requirements.txt
```

### ▶️ Como Usar

Execute o script principal a partir do terminal:

```bash
python3 DOS_viewer.py
```
Uma tela de apresentação será exibida. Clique em "Seguir" para abrir a interface principal.
Utilize os botões "Carregar Nível de Fermi" e "Carregar Arquivos PDOS" para importar seus dados e começar a visualizar seus gráficos.

## 📊 Fluxo de Uso
```mermaid
flowchart TD
    A[Início] --> B["Carregar Nível de Fermi (.bands)"]
    B --> C["Carregar Arquivos PDOS (.dat)"]
    C --> D[Personalizar Curvas]
    D --> D1["Alterar nome da legenda"]
    D --> D2["Mudar cor da curva"]
    D --> E[Ajustar Gráfico]
    E --> E1["Inverter eixos (DOS vs Energia)"]
    E --> E2["Definir limites de Energia e DOS"]
    E --> E3["Definir espaçamento dos eixos"]
    E --> F[Exportar Gráfico]
    F --> F1["Salvar como PNG"]
    F --> F2["Salvar como PDF"]
    F --> G[Fim]

```

### 🤝 Colaborações

Se você encontrar algum bug ou tiver sugestões para o projeto, sinta-se à vontade para abrir uma issue ou um pull request.

## 📜 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).
Veja o arquivo `LICENSE` para mais detalhes.
---

## ⚛️ Conheça o Nosso Grupo GNC

![](https://github.com/HenriqueDFT/DOS-viewer/blob/main/qr.png)

 '''   
     Autor: Henrique Lago L.
     Este software foi desenvolvido com intuito de auxiliar e otimizar os trabalhos na área da teoria do funcional da densidade(DFT).
     Foi desenvolvido durante minha iniciação científica voluntária,sob orientação do professor Dr.Ramon Sampaio F. na Universidade Federal 
     do Piauí (UFPI),como membro do grupo de Nanofísica Computacional (GNC/UFPI)

   
