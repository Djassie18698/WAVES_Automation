# WAVES - Werkplekken Automatiseren Via Efficiënte Scripts

Welkom bij het WAVES-project! Dit project is ontwikkeld als onderdeel van een stage bij Zuyd Hogeschool en richt zich op het automatiseren van het opzetten, beheren en afbreken van virtuele werkplekken binnen de SURF Research Cloud-omgeving.

## 🔧 Wat is WAVES?

WAVES staat voor **Werkplekken Automatiseren Via Efficiënte Scripts**. Het doel van dit project is om het handmatige proces van het inrichten van werkplekken te vervangen door een volledig geautomatiseerde workflow. Dit wordt gerealiseerd door gebruik te maken van:

- **Python** voor scripting en API-integraties
- **Ansible** voor configuratiebeheer en provisioning
- **GitHub** als opslagplaats en trigger voor updates
- **SURF Research Cloud API** voor het aanmaken en beheren van werkplekken

## 🧠 Hoe werkt het?

De workflow verloopt als volgt:

1. **Monitoren van GitHub:** Er wordt geluisterd naar commits in een opgegeven repository.
2. **Automatisch aanmaken van VM's:** Bij een wijziging wordt automatisch een nieuwe workspace aangemaakt via de SURF API.
3. **Configureren via Ansible:** Zodra de VM actief is, wordt deze geconfigureerd met een Ansible playbook.
4. **Uitvoeren van code:** De code uit de GitHub repo wordt automatisch uitgevoerd op de workspace.
5. **Resultaten terugzetten:** Resultaten worden automatisch teruggepushd naar de GitHub-repository.
6. **Automatisch verwijderen:** De VM wordt verwijderd zodra het werk klaar is.

## 📁 Belangrijke bestanden

| Bestand | Beschrijving |
|--------|--------------|
| `fullmain.py` | Hoofdscript dat alles aanstuurt: tokens, VM-aanmaak, Ansible-oproep, etc. |
| `fullmainlogging.py` | Variant van het hoofdscript met uitgebreide logging. |
| `IDFinder_basic.py` | Haalt het IP-adres van de nieuwe workspace op en past de Ansible-inventory aan. |
| `setup_vm.yml` | Het Ansible playbook dat de workspace configureert. |
| `inventory.ini` | Dynamisch gegenereerde Ansible-inventory met de juiste SSH-instellingen. |
| `gitdownloader.yml` | Ansible taak voor het clonen en terugpushen van een GitHub-repo. |
| `data/` | Map voor tijdelijke of permanente data (zoals logs of outputbestanden). |
| `requirements.txt` | Bevat de Python-afhankelijkheden voor dit project. |

## 🔨 Installatie

1. Installeer de afhankelijkheden:
   ```bash
   pip install -r requirements.txt
   ```
2. Start het script:
   ```bash
   python fullmain.py
   ```

## 🔐 Authenticatie

Voor dit project zijn twee tokens nodig:
- **SURF API Key**: Voor het aanmaken en beheren van werkplekken
- **GitHub Token**: Voor toegang tot de repository (lezen/schrijven)

Deze worden gevraagd bij het starten van `fullmain.py` en **worden niet opgeslagen** in het script of in plaintext-bestanden.

## 💡 Mogelijke uitbreidingen

- Ondersteuning voor meerdere repositories
- Logging en monitoring via een dashboard
- Integratie met GitHub Actions of GitLab CI/CD
- Gebruikersinterface (GUI) voor minder technische gebruikers

## 📜 Licentie

Dit project is ontwikkeld voor educatieve doeleinden tijdens een stage aan Zuyd Hogeschool. Gebruik, aanpassing en herdistributie is toegestaan met bronvermelding.

---

> Ontwikkeld door Dean Nellessen  
> Stage bij het DI-Lab (Brightlands), 2025  
> Opleiding: AD-ICT - Zuyd Hogeschool
