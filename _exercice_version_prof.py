#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import csv
import os
import time
import configparser

import inputs
import mido


notes_per_octave = 12
default_velocity = 80


def build_note_dictionaries(note_names, add_octave_no=True):
	c0_midi_no = 12 # Plus basse note sur les pianos est La 0, mais on va commencer à générer les noms sur Do 0

	midi_to_name = {}
	name_to_midi = {}
	# Pour chaque octave de 0 à 8 (inclus). On va générer tout l'octave 8, même si la dernière note du piano est Do 8.
	for octave in range(8+1):
		# Pour chaque note de l'octave :
		for note in range(notes_per_octave):
			# Calculer le numéro MIDI de la note et ajouter aux deux dictionnaires.
			midi_no = c0_midi_no + octave * notes_per_octave + note
			# Ajouter le numéro de l'octave au nom de la note si add_octave_no est vrai.
			full_note_name = note_names[note] + (str(octave) if add_octave_no else "")
			midi_to_name[midi_no] = full_note_name
			# Garder les numéros de notes dans name_to_midi entre 0 et 11 si add_octave_no est faux.
			name_to_midi[full_note_name] = midi_no if add_octave_no else midi_no % notes_per_octave
	return midi_to_name, name_to_midi

def send_note_on(note_name, name_to_midi, midi_outputs):
	# On construit un message MIDI qui appuie la note.
	msg = mido.Message("note_on", note=name_to_midi[note_name], velocity=default_velocity)
	# On envoie le message sur chaque sortie.
	for o in midi_outputs:
		o.send(msg)

def send_note_off(note_name, name_to_midi, midi_outputs):
	# On construit un message MIDI qui relâche la note.
	msg = mido.Message("note_off", note=name_to_midi[note_name])
	# On envoie le message sur chaque sortie.
	for o in midi_outputs:
		o.send(msg)

def build_note_callbacks(note_name, name_to_midi, midi_outputs):
	# Construire des callbacks pour bouton appuyé et relâché (retournés en tuple) en utilisant `send_note_on` et `send_note_off`.
	# Ces callbacks ne prennent aucun paramètre.
	def action_fn_pressed():
		send_note_on(note_name, name_to_midi, midi_outputs)
	def action_fn_released():
		send_note_off(note_name, name_to_midi, midi_outputs)
	return action_fn_pressed, action_fn_released

def build_chord_callbacks(chord, chord_notes, name_to_midi, midi_outputs):
	# Construire des callbacks pour bouton appuyé et relâché en utilisant `send_note_on` et `send_note_off`. On veut appuyer ou relâcher chaque note de l'accord.
	# Ces callbacks ne prennent aucun paramètre.
	def action_fn_pressed():
		for note in chord_notes[chord]:
			send_note_on(note, name_to_midi, midi_outputs)
	def action_fn_released():
		for note in chord_notes[chord]:
			send_note_off(note, name_to_midi, midi_outputs)
	return action_fn_pressed, action_fn_released

def build_custom_action_callbacks(action_name, custom_actions, midi_outputs):
	# On prend en paramètre le nom de l'action qui sera écrite dans le fichier de commandes, le dictionnaire des actions personnalisées et la liste des sorties MIDI à utiliser
	# Chaque action personnalisée est une fonction qui prend en paramètre une liste de sorties MIDI
	# Par exemple, la clé "foo" dans le dictionnaire serait elle-même un dictionnaire de la forme {True: une_fonction, False: une_autre_fonction}, où `une_fonction` doit être appelée quand le bouton de la manette est appuyé, et `une_autre_fonction` est appuyée quand le bouton est relâché.
	# Construire des callbacks pour bouton appuyé et relâché.
	pressed_fn, released_fn = None, None
	# Si l'action a une fonction donnée pour bouton appuyé :
	if True in custom_actions[action_name] and custom_actions[action_name][True] is not None:
		# On lie cette fonction aux sorties MIDI.
		def action_fn_pressed():
			custom_actions[action_name][True](midi_outputs)
		pressed_fn = action_fn_pressed
	# Si l'action a une fonction donnée pour bouton relâché :
	if False in custom_actions[action_name] and custom_actions[action_name][False] is not None:
		# On lie cette fonction aux sorties MIDI.
		def action_fn_released():
			custom_actions[action_name][False](midi_outputs)
		released_fn = action_fn_released
	return pressed_fn, released_fn

def load_input_mappings(filename, name_to_midi, chord_notes, midi_outputs, custom_actions={}):
	# On ouvre et lit le fichier INI
	config = configparser.ConfigParser()
	config.read(filename)
	# On prend la section "gamepad" (qui est probablement la seule)
	gamepad_section = config["gamepad"]

	# On fait un dictionnaire 
	mappings = {}
	for gamepad_input in gamepad_section:
		action_name = gamepad_section[gamepad_input]
		# Construire des callbacks pour l'action appropriée et l'ajouter au mapping.
		pressed_fn, released_fn = None, None
		# On veut construire les callbacks appropriés selon le nom de l'action.
		# Si l'action est un nom de note (présent dans `name_to_midi`):
		if action_name in name_to_midi:
			# On construit les callbacks qui joue une note
			pressed_fn, released_fn = build_note_callbacks(action_name, name_to_midi, midi_outputs)
		# Si l'action est un nom d'accord (présent dans `chord_notes`):
		elif action_name in chord_notes:
			# On construit les callbacks qui joue un accord
			pressed_fn, released_fn = build_chord_callbacks(action_name, chord_notes, name_to_midi, midi_outputs)
		# Si l'action est une action personnalisée (présent dans `custom_actions`):
		elif action_name in custom_actions:
			# On construit les callbacks qui exécutent une action personnalisée (une fonction présente dans le dictionnaire)
			pressed_fn, released_fn = build_custom_action_callbacks(action_name, custom_actions, midi_outputs)
		# On ajoute au dictionnaire des mappings où la clé est le nom du contrôle de manette (`gamepad_input`) et la valeur est un dictionnaire où on a les clés True et False et les valeurs pressed_fn et released_fn associées.
		mappings[gamepad_input] = {True: pressed_fn, False: released_fn}

	return mappings


def main():
	# Affiche les ports MIDI que mido reconnait.
	available_input_ports = mido.get_input_names()
	available_output_ports = mido.get_output_names()
	print(f"Liste des ports d'entrée MIDI disponibles : {available_input_ports}")
	print(f"Liste des ports de sortie MIDI disponibles : {available_output_ports}")

	# On choisit une manette de jeu que la librairie inputs nous fournit.
	gamepad = inputs.devices.gamepads[0]
	# On ouvre les sorties MIDI qui nous intéressent.
	midi_outputs = [mido.open_output("3- UM-ONE 1")]

	# On lit le fichier JSON qui contient les informations musicales.
	notes_data = json.load(open("notes.json", "r", encoding="utf-8"))
	# On extrait les noms des notes en français.
	note_names = notes_data["solfeggio_names"]
	# On extrait les notes des accords connus.
	chords = notes_data["chords"]
	# On construit nos dictionnaires de traduction de nom à MIDI et vice-versa.
	midi_to_name, name_to_midi = build_note_dictionaries(note_names)

	# On se crée deux actions custom qui ne font qu'afficher des messages
	def foo0(midi_outputs):
		print("henlo")
	def foo1(midi_outputs):
		print("k bye")

	# On crée des actions custom qui contrôle la pédale de résonnance du piano
	def sustain_on(midi_outputs):
		# Message MIDI correspondant à la pédale appuyée.
		msg = mido.Message("control_change", channel=0, control=64, value=127)
		# On envoit sur chaque sortie.
		for o in midi_outputs:
			o.send(msg)
	def sustain_off(midi_outputs):
		# Message MIDI correspondant à la pédale relâchée.
		msg = mido.Message("control_change", channel=0, control=64, value=0)
		# On envoit sur chaque sortie.
		for o in midi_outputs:
			o.send(msg)

	# Dans le dictionnaire d'actions, la clé est le nom de la commande, et la valeur est un dictionnaire.
	# Dans celui-ci, la clé est True pour appuyé et False pour relâché et la valeur est une fonction à exécuter (ou None si rien à faire).
	custom_actions = {
		"foo": {True: foo0, False: foo1},
		# Dans le fichier INI, la ligne `BTN_TR = sustain` ferait en sorte que d'appuyer le bouton LB va contrôler la pédale.
		"sustain": {True: sustain_on, False: sustain_off}
	}

	# On charge la configuration du fichier INI.
	mappings = load_input_mappings("input.ini", name_to_midi, chords, midi_outputs, custom_actions)
	# On affiche le contenu juste pour nous aider.
	print("mappings =", json.dumps(mappings, indent=2, default=str))

	# Pour toujours...
	while True:
		# Pour chaque bouton de manette reçu :
		for e in gamepad.read():
			# On prend le code du bouton (son nom) et on en ignore la casse.
			btn = e.code.lower()
			# On prend l'état du bouton (1 = appuyé, 0 = relâché).
			pressed = bool(e.state)
			# Si c'est un bouton qu'on connait (dans notre configuration).
			if btn in mappings:
				# On obtient les callbacks associés.
				callbacks = mappings[btn]
				# On appelle le callback associé à l'état du bouton (si applicable).
				if pressed in callbacks and callbacks[pressed] is not None:
					mappings[btn][pressed]()
				# On affiche le bouton et son état, juste pour nous aider.
				print(btn, pressed)

if __name__ == "__main__":
	main()
