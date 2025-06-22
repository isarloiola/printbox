#!/bin/bash

echo "Criando ambiente virtual..."
python3 -m venv venv

echo "Ativando ambiente virtual..."
source venv/bin/activate

echo "Atualizando pip..."
pip install --upgrade pip

echo "Instalando pacotes necessários..."
pip install pillow qrcode ttkthemes PyPDF2 tkcalendar

echo "Setup concluído!"
echo "Para ativar o ambiente virtual futuramente, rode:"
echo "source venv/bin/activate"
