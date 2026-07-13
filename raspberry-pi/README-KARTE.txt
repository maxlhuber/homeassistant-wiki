HOME-ASSISTANT-WIKI – ERSTER START
=================================

1. MicroSD-Karte in den Raspberry Pi 4B einsetzen.
2. Der Raspberry Pi verbindet sich automatisch mit dem vorbereiteten WLAN.
   Ein Netzwerkkabel kann alternativ oder zusätzlich verwendet werden.
3. Strom anschließen und 10 bis 20 Minuten warten.
4. Danach im Browser öffnen:

   http://homeassistant-wiki.local/

Während des ersten Starts werden die benötigten Pakete aus dem Internet
installiert. Der Raspberry Pi startet dabei einmal automatisch neu.

SSH-ZUGANG (nur mit dem Schlüssel auf MAX-PC)
----------------------------------------------

Benutzer:  wikiadmin
Hostname:  homeassistant-wiki.local
Schlüssel: C:\Users\maxlh\.ssh\homeassistant-wiki_ed25519

Beispiel:
ssh -i C:\Users\maxlh\.ssh\homeassistant-wiki_ed25519 wikiadmin@homeassistant-wiki.local

Auf der Startpartition zeigt WIKI-STATUS.txt nach dem ersten Start an,
ob die Grundkonfiguration bzw. die Wiki-Installation abgeschlossen ist.
