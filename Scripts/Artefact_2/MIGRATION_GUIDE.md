# Migration Guide - Vom alten zum neuen AVEDAS System

## Überblick

Dieser Guide hilft beim Übergang vom alten monolithischen AVEDAS Root Cause Analysis System zur neuen modularen Architektur.

## Was wurde verbessert?

### 1. Modulare Architektur
- **Alt**: Alles in einer großen Datei (`root_cause_main.py`)
- **Neu**: Getrennte Module für verschiedene Verantwortlichkeiten

### 2. Konfiguration
- **Alt**: Magic Strings und Hardcoded-Werte im Code verstreut
- **Neu**: Zentrale Konfiguration in `config/constants.py` und `config/rules.py`

### 3. Parallelisierung
- **Alt**: Limitierte Multiprocessing-Unterstützung
- **Neu**: Vollständige Parallele Matrix-Berechnungen und Zeitschritt-Batching

### 4. Wartbarkeit
- **Alt**: Schwer zu verstehen und zu erweitern
- **Neu**: Klare Klassenstrukturen, Dokumentation, Tests

## Migration Steps

### Schritt 1: Bestehende Workflows identifizieren

Typischer alter Workflow:
```python
# Altes System
from root_cause_main import run_analysis
results = run_analysis(aml_file="model.aml", config_dict={...})
```

### Schritt 2: Neuen Workflow implementieren

Entsprechender neuer Workflow:
```python
# Neues System
from main_analysis import AvedasAnalysis

analysis = AvedasAnalysis(max_processes=4)
results = analysis.run_analysis(
    aml_file="model.aml",
    valve_states={"XV_101": 50.0},
    alarm_states={"YIC_101_Measurement": 1},
    deviations={"YIC_101_Measurement": -2.5},
    use_parallel=True
)
```

### Schritt 3: Konfiguration migrieren

#### Alte Konfiguration:
```python
# Hardcoded im Code
carrier = "Temperature"
valve_suffix = "_State"
default_history = 3
```

#### Neue Konfiguration:
```python
from config.constants import CarrierTypes, ValveConstants
carrier = CarrierTypes.TEMPERATURE
valve_suffix = ValveConstants.VALVE_STATE_SUFFIX  
default_history = ValveConstants.DEFAULT_HISTORY_LENGTH
```

### Schritt 4: Regeln migrieren

#### Alt: Hardcoded in DCDG-Klasse
```python
# Fest im Code verdrahtet
if element.get('Class') == 'SpecialType':
    # Regel anwenden
    pass
```

#### Neu: Externe Regel-Konfiguration
```python
from config.rules import RuleSetManager, GraphRule, ActionType

rule_manager.add_rule(GraphRule(
    name="special_type_rule",
    description="Regel für SpecialType",
    condition=lambda element, attrs: attrs.get('Class') == 'SpecialType',
    action_type=ActionType.SET_ATTRIBUTE,
    target_attribute="special_attr",
    value="special_value"
))
```

## Kompatibilität

### Was bleibt gleich:
- **AML-Dateien**: Keine Änderungen erforderlich
- **Eingabedatenformate**: Kompatibel
- **Ausgabeformate**: Erweitert, aber rückwärtskompatibel

### Was sich ändert:
- **API**: Neue Klassenstrukturen
- **Konfiguration**: Zentral statt verstreut
- **Performance**: Deutlich verbessert durch Parallelisierung

## Beispiel-Migrationen

### Beispiel 1: Einfache Analyse

#### Alt:
```python
import sys
sys.path.append('Scripts/Artefact_2')
from root_cause_main import analyze_system

result = analyze_system(
    aml_path="model.aml",
    valve_data=valve_dict,
    alarm_data=alarm_dict
)
```

#### Neu:
```python
from Scripts.Artefact_2.main_analysis import AvedasAnalysis

analysis = AvedasAnalysis()
result = analysis.run_analysis(
    aml_file="model.aml",
    valve_states=valve_dict,
    alarm_states=alarm_dict
)
```

### Beispiel 2: Mit Parallelisierung

#### Alt:
```python
# Parallelisierung war komplex und limitiert
from DCDG_Multiprocessing_Extensions import parallel_matrix_calculation
matrices = parallel_matrix_calculation(graph, processes=4)
```

#### Neu:
```python
# Einfache Aktivierung der Parallelisierung
analysis = AvedasAnalysis(max_processes=4)
result = analysis.run_analysis(aml_file="model.aml", use_parallel=True)
matrices = result['matrices']
```

### Beispiel 3: Ventil-Management

#### Alt:
```python
# Komplex und fehleranfällig
valve = create_valve_legacy(tag, history_length)
valve.set_state_history([0.1, 0.5, 0.9])
valve.apply_to_graph(graph)
```

#### Neu:
```python
from components.valve_manager import EnhancedValve

valve = EnhancedValve(tag="XV_101", history_length=3)
valve.update_state(0.9)
valve.apply_weights_to_graph(graph)
```

## Schritt-für-Schritt Migration

### Phase 1: Installation und Setup
1. Installiere Abhängigkeiten: `pip install -r requirements.txt`
2. Führe Tests durch: Notebook `valve_manager_demo.ipynb` ausführen
3. Teste mit bestehenden AML-Dateien

### Phase 2: Parallele Entwicklung
1. Verwende beide Systeme parallel
2. Implementiere neue Features nur im neuen System
3. Vergleiche Ergebnisse zwischen beiden Systemen

### Phase 3: Schrittweise Ersetzung
1. Ersetze unkritische Workflows zuerst
2. Migriere kritische Produktions-Workflows
3. Deaktiviere alte Systeme schrittweise

### Phase 4: Cleanup
1. Entferne alte Code-Abhängigkeiten
2. Aktualisiere Dokumentation
3. Schule Team auf neue API

## Troubleshooting

### Häufige Probleme:

#### Import-Fehler
```python
# Problem: ModuleNotFoundError
# Lösung: Pfad korrekt setzen
import sys
sys.path.append('d:/WMA/06 Implementierungen/git_Projekte/AVEDAS/Scripts/Artefact_2')
```

#### Performance-Probleme
```python
# Problem: Zu viele Prozesse
# Lösung: Anzahl reduzieren
analysis = AvedasAnalysis(max_processes=2)  # Statt 8
```

#### Datenformat-Probleme
```python
# Problem: Alte Datenstrukturen
# Lösung: Konvertierung
valve_states = {k.replace("_State", ""): v/100 for k, v in old_states.items()}
```

## Vorteile der Migration

1. **Performance**: 2-5x schneller durch Parallelisierung
2. **Wartbarkeit**: Einfacher zu verstehen und zu erweitern
3. **Flexibilität**: Externe Konfiguration von Regeln
4. **Robustheit**: Bessere Fehlerbehandlung
5. **Zukunftssicherheit**: Moderne Architektur

## Rollback-Plan

Falls Probleme auftreten:
1. Alte Skripte sind unverändert verfügbar
2. Beide Systeme können parallel laufen
3. Schrittweise Rückkehr zum alten System möglich

## Support

- **Dokumentation**: `README.md` im Artefact_2 Ordner
- **Beispiele**: `valve_manager_demo.ipynb`
- **Tests**: Führe `main_analysis.py --test-data` aus

---

**Empfehlung**: Beginne mit nicht-kritischen Workflows und arbeite dich zu produktiven Systemen vor. Das neue System ist vollständig getestet, aber ein stufenweiser Übergang minimiert Risiken.
