@echo off
rem Abre o controle do celular no Chrome em modo demonstracao (sem Pi), em tamanho de celular deitado
start "" chrome --new-window --window-size=900,460 "file:///%~dp0controle.html?demo"
