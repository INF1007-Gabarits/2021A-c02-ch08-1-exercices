# Manettes et claviers (chapitre 8.1)

Avant de commencer. Consulter les instructions à suivre dans [instructions.md](instructions.md)

## Appareils d'entrée/sortie 

Dans cette série d'exercices, nous utiliserons un clavier MIDI comme au chapitre 7.2, mais en sortie plutôt qu'en entrée. Nous utiliserons aussi une manette de jeu (de style Xbox) en entrée grâce à la librairie [inputs](https://pypi.org/project/inputs/).

## 1. Associations MIDI, notes et accords

Dans les exercices du chapitre 7.2, Nous avons vu généré un dictionnaire d'association entre des notes et des numéros MIDI, ainsi que des accords avec des notes. En réutilisant `build_note_dictionaries` du chap 7.2, nous allons maintenant charger ces éléments à partir d'un fichier JSON avec une structure particulière. Nous allons ensuite bâtir nos associations de notes MIDI grâce au contenu des dictionnaires.

Au lieu d'avoir ceci dans le code:
```python
english_names = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
solfeggio_names = ["Do", "Réb", "Ré", "Mib", "Mi", "Fa", "Fa#", "Sol", "Lab", "La", "Sib","Si"]
chords = {
    "Do majeur": ("Do", "Mi", "Sol"),
    "Fa majeur": ("Fa", "La", "Do"),
    "Sol majeur": ("Sol", "Si", "Ré"),
    "La mineur": ("La", "Do", "Mi")
}
```
Nous avons un JSON comme ceci:
```json
{
  "english_names": [ "C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B" ],
  "solfeggio_names": [ "Do", "Réb", "Ré", "Mib", "Mi", "Fa", "Fa#", "Sol", "Lab", "La", "Sib", "Si" ],
  "chords": {
    "Do majeur": [
      "Do3",
      "Mi3",
      "Sol3"
    ],
    "Fa majeur": [
      "Do3",
      "Fa3",
      "La3"
    ],
    "Sol majeur": [
      "Si2",
      "Ré3",
      "Sol3"
    ],
    "La mineur": [
      "Do3",
      "Mi3",
      "La3"
    ]
  }
}
```

Il nous faut donc charger le contenu de ce fichier et ensuite l'utiliser de la même façon que dans l'exercice du chapitre 7.2, c'est-à-dire dans la fonction `build_note_dictionnaries`

```python
notes_data = CHARGER LE CONTENU DU JSON
note_names = CE QU'IL Y A DANS "solfeggio_names"
midi_to_name, name_to_midi = build_note_dictionaries(note_names)
chords = CE QU'IL Y A DANS "chords"
```

## 2. Configuration d'actions sur boutons de manettes

Cet exercice est somme toute assez compliqué, et il y a définitivement plusieurs façons d'en arriver à une solution.

On veut ultimement pouvoir faire jouer des notes et des accords sur un piano en sortie à partir de boutons sur une manette de jeu en entrée. Par exemple, le bouton A joue un do majeur, le bouton X joue un ré mineur, le bouton R joue un do, et ainsi de suite.

On veut aussi pouvoir exécuter des actions quelquonques (des fonctions) sur les boutons de la manette.

### 2.1. Structure d'un fichier INI

Les fichiers INI, ou de façon plus générale les fichiers de *config* ([plus d'info](https://fr.wikipedia.org/wiki/Fichier_INI)), permettent d'enregistrer des configurations dans un format assez simple. La forme générale est :

```ini
[Nom d'une section]
Variable = La valeur de la variable
UneAutreVariable = Une autre valeur
; Un commentaire (les commentaires commencent par un point-virgule)

[Nom d'une autre section]
Variable = La valeur de la variable
```

Nous allons nous servir d'un fichier INI pour contenir la configuration des contrôles. C'est en fait une pratique assez courante dans le domaine des jeux vidéos d'utiliser ce format de fichier pour les options de jeux de toute sorte. Dans notre cas, nous avons un fichier qui ressemble à ceci : 

```ini
[gamepad]
BTN_TR = Do4
BTN_SOUTH = Do majeur
BTN_WEST = Ré mineur
BTN_EAST = La mineur
BTN_NORTH = Sol majeur
BTN_TL = sustain
```

Le nom de la section qui va contenir nos contrôle est `gamepad`. S'il y a d'autres sections présentes dans le fichier, elles seront ignorées. Dans cette section, chaque ligne représente un bouton et la commande associée. Par exemple, `BTN_SOUTH` (qui est le bouton A sur une manette de Xbox) va jouer un do majeur et le `BTN_TL` (bouton LB sur manette Xbox) va activer la pédale de résonnance.

Il nous faut donc passer sur toutes les configurations de boutons dans le fichier et les ajouter dans un dictionnaire où la clé est le nom du bouton et la valeur est l'action à exécuter. Nous allons faire des fonctions de rappel pour contenir ces actions. Il nous faut donc construire des callbacks qui peuvent, par exemple, jouer un accord.

### 2.2. Construire des callbacks à appeler sur des boutons

Il y a plusieurs types de callbacks que nous avons besoin de construire : ceux qui jouent une note unique, ceux qui jouent un accord (plusieurs notes en même temps) et ceux qui exécutent une action quelquonque.

#### 2.2.1 Note unique

La fonction `build_note_callbacks` prend en paramètre le nom de la note à jouer, le dictionnaire de conversion de nom de note à numéro MIDI et la liste des sortie MIDI sur lesquelles envoyer la note. On retourne deux fonctions sans paramètre qui appuie et relâche, respectivement, la note donnée sur les sorties données. Voici un exemple d'utilisation de cette fonction :

```python
note_names = ["Do", "Réb", "Ré", "Mib", "Mi", "Fa", "Fa#", "Sol", "Lab", "La", "Sib", "Si"]
midi_to_name, name_to_midi = build_note_dictionaries(note_names)
midi_outputs = [
    mido.open_output("Le port MIDI d'un piano"),
    mido.open_output("Un autre port MIDI")
]
# On obtient nos deux callbacks qui jouent do 4 (le do du milieu)
note_on, note_off = build_note_callbacks("Do4", name_to_midi, midi_outputs)
# `note_on` appuie sur un do
note_on()
time.sleep(1.0)
# On relâche do
note_off()
```
On remarque que les fonctions de rappel ne prennent rien en paramètre et connaissent leur note à travers leur fermeture lexicale.

#### 2.2.2 Accord

Dans `build_chord_callbacks` on fait essentiellement la même chose que dans `build_note_callbacks`, mais en jouant plusieurs notes en même temps. On prend donc en paramètre une liste de noms de note à jouer plutôt qu'une note unique. Exemple d'utilisation : 

```python
note_names = ["Do", "Réb", "Ré", "Mib", "Mi", "Fa", "Fa#", "Sol", "Lab", "La", "Sib", "Si"]
midi_to_name, name_to_midi = build_note_dictionaries(note_names)
midi_outputs = [
    mido.open_output("Le port MIDI d'un piano"),
    mido.open_output("Un autre port MIDI")
]
# On obtient nos deux callbacks qui jouent un do majeur (do, mi, sol)
chord_on, chord_off = build_chord_callbacks(("Do3", "Mi3", "Sol3"), name_to_midi, midi_outputs)
# `chord_on` appuie un do majeur (do, mi, sol)
chord_on()
time.sleep(1.0)
# On relâche do majeur
chord_off()
```

#### 2.2.3 Action personnalisée

On veut aussi pouvoir exécuter des fonctions quelquonques sur un bouton de manette. `build_custom_action_callbacks` prend en paramètre le nom de l'action qui sera écrite dans le fichier de commandes, le dictionnaire des actions personnalisées et la liste des sorties MIDI à utiliser. On retourne deux fonctions de rappel sans paramètres qui peuvent être à `None` s'il n'y a rien à faire dans un cas ou dans l'autre. Les fonctions dans le dictionnaire doivent prendre en paramètre les sorties MIDI. Voici un exemple d'utilisation où on veut créer deux callbacks qui affichent des messages dans la console :

```python
# Dans cet exemple, on ne fait rien avec la sortie MIDI
def foo0(midi_outputs):
    print("henlo")
def foo1(midi_outputs):
    print("k bye")

# Dans le dictionnaire, la clé est le nom de la commande, et la valeur est un dictionnaire où
# la clé est True pour appuyé et False pour relâché et la valeur est une fonction à exécuter.
custom_actions = {
    "foo": {True: foo0, False: foo1}
}
action_on, action_off = build_custom_action_callbacks("foo", custom_actions, [])
# On affiche hello
action_on()
# On affiche bye
action_off()
```

Là, on pourrait se demander pourquoi on lie toujours les sorties MIDI aux callbacks plutôt que de créer des callbacks qui prennent en paramètre les sorties et les passer à chaque fois qu'on les appelle. C'est tout simplement un choix qu'on a fait, mais les deux façons de faire sont toutes aussi valides, elles offrent des options différentes.

### 2.3. Charger la configuration

Maintenant que nous pouvons construire tous les types de callback dont nous avons besoin, on peut lire le fichier INI et créer notre dictionnaire de contrôles. La fonction `load_input_mappings` prend en paramètre le nom du fichier de configuration et les autres trucs nécessaire à la construction des callbacks. Le dictionnaire retourné a la forme :

```python
mappings = {
    "Nom d'un bouton de la manette": {
        True: <Callback à appeler quand le bouton est appuyé>,
        False: <Callback à appeler quand le bouton est relâché>
    },
    "Nom d'un autre bouton de la manette": {
        True: <Callback à appeler quand le bouton est appuyé>,
        False: <Callback à appeler quand le bouton est relâché>
    },
    Et ainsi de suite...
}
```

Par exemple, le fichier INI :

```ini
[gamepad]
BTN_SOUTH = Do majeur
BTN_WEST = Do4
BTN_EAST = foo
```

donnerait le dictionnaire suivant (en posant qu'on a l'action `foo` de l'exemple de 2.2.3) :

```python
mappings = {
    "btn_south": {
        True: <Callback qui joue do majeur>,
        False: <Callback relâche do majeur>
    },
    "btn_west": {
        True: <Callback qui joue do 4>,
        False: <Callback relâche do 4>
    },
    "btn_east": {
        True: <Callback qui affiche "henlo">,
        False: <Callback qui affiche "k bye">
    }
}
```

On met tout en minuscule pour ignorer la casse.

## 3. Exécuter la configuration

On fait une boucle infinie qui traite les événements de la manette de jeu et qui exécute les actions associées. Remarquez que dans ce cas-ci, on fait du *polling*, même si on a des fonctions de rappel. En effet, dans notre les fonction de rappel permettent tout simplement d'avoir un dictionnaire qui associe les boutons à des actions, sans que ce soit nécessairement un exécution en parallèle.
