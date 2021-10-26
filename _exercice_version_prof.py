#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mido
import json
import csv
import os
import time
import configparser
from copy import deepcopy

import inputs
import mido


notes_per_octave = 12


def build_note_dictionaries(note_names, add_octave_no=True):
	c0_midi_no = 12 # Plus basse note sur les pianos est La 0, mais on va commencer à générer les noms sur Do 0

	midi_to_name = {}
	name_to_midi = {}
	# Pour chaque octave de 0 à 8 (inclus). On va générer tout l'octave 8, même si la dernière note du piano est Do 8
	for octave in range(8+1):
		# Pour chaque note de l'octave
		for note in range(notes_per_octave):
			# Calculer le numéro MIDI de la note et ajouter aux deux dictionnaires
			midi_no = c0_midi_no + octave * notes_per_octave + note
			# Ajouter le numéro de l'octave au nom de la note si add_octave_no est vrai
			full_note_name = note_names[note] + (str(octave) if add_octave_no else "")
			midi_to_name[midi_no] = full_note_name
			# Garder les numéros de notes dans name_to_midi entre 0 et 11 si add_octave_no est faux
			name_to_midi[full_note_name] = midi_no if add_octave_no else midi_no % notes_per_octave
	return midi_to_name, name_to_midi

def send_note_on(note_name, name_to_midi, midi_outputs):
	msg = mido.Message("note_on", note=name_to_midi[note_name], velocity=default_velocity)
	for o in midi_outputs:
		o.send(msg)

def send_note_off(note_name, name_to_midi, midi_outputs):
	msg = mido.Message("note_off", note=name_to_midi[note_name])
	for o in midi_outputs:
		o.send(msg)

def build_note_callbacks(note_name, name_to_midi, midi_outputs):
	# Construire des callbacks pour bouton appuyé et relâché en utilisant `send_note_on` et `send_note_off`
	# Ces callbacks ne prennent aucun paramètre
	return action_fn_pressed, action_fn_released

def build_chord_callbacks(chord, chord_notes, name_to_midi, midi_outputs):
	# Construire des callbacks pour bouton appuyé et relâché en utilisant `send_note_on` et `send_note_off`. On veut appuyer ou relâcher chaque note de l'accord.
	# Ces callbacks ne prennent aucun paramètre
	return action_fn_pressed, action_fn_released

def build_custom_action_callbacks(action_name, custom_actions, midi_outputs):
	# On prend en paramètre le nom de l'action qui sera écrite dans le fichier de commandes, le dictionnaire des actions personnalisées et la liste des sorties MIDI à utiliser
	# Chaque action personnalisée est une fonction qui prend en paramètre une liste de sorties MIDI
	# Par exemple, la clé "foo" dans le dictionnaire serait elle-même un dictionnaire de la forme {True: une_fonction, False: une_autre_fonction}, où `une_fonction` doit être appelée quand le bouton de la manette est appuyé, et `une_autre_fonction` est appuyée quand le bouton est relâché.
	# Construire des callbacks pour bouton appuyé et relâché.
	return pressed_fn, released_fn

def load_input_mappings(filename, name_to_midi, chord_notes, midi_outputs, custom_actions={}):
	# On ouvre et lit le fichier INI
	# On prend la section "gamepad" (qui est probablement la seule)
	gamepad_section = {} # TODO

	mappings = {}
	for gamepad_input in gamepad_section:
		action_name = gamepad_section[gamepad_input]
		pressed_fn, released_fn = None, None
		# On veut construire les callbacks appropriés selon le nom de l'action.
		# Si l'action est un nom de note (présent dans `name_to_midi`):
			# On construit les callbacks qui joue une note
		# Si l'action est un nom d'accord (présent dans `chord_notes`):
			# On construit les callbacks qui joue un accord
		# Si l'action est une action personnalisée (présent dans `custom_actions`):
			# On construit les callbacks qui exécutent une action personnalisée (une fonction présente dans le dictionnaire)
		# On ajoute au dictionnaire des mappings où la clé est le nom du contrôle de manette (`gamepad_input`) et la valeur est un dictionnaire où on a les clés True et False et les valeurs pressed_fn et released_fn associées.
	return mappings


def main():
	# Affiche les ports MIDI que mido reconnait.
	available_input_ports = mido.get_input_names()
	available_output_ports = mido.get_output_names()
	print(f"Liste des ports d'entrée MIDI disponibles : {available_input_ports}")
	print(f"Liste des ports de sortie MIDI disponibles : {available_output_ports}")

	gamepad = inputs.devices.gamepads[0]
	midi_outputs = (mido.open_output("UM-ONE 3"), mido.open_output("UnPortMIDI 4"))
	midi_input = mido.open_input("UM-ONE 0")

	note_names = {} # Charger du JSON
	midi_to_name, name_to_midi = build_note_dictionaries([]) # Charger du JSON
	chords = {} # Charger du JSON

	def foo0(midi_outputs):
		print("henlo")
	def foo1(midi_outputs):
		print("k bye")
	def sustain_on(midi_outputs):
		msg = mido.Message("control_change", channel=0, control=64, value=127)
		for o in midi_outputs:
			o.send(msg)
	def sustain_off(midi_outputs):
		msg = mido.Message("control_change", channel=0, control=64, value=0)
		for o in midi_outputs:
			o.send(msg)

	custom_actions = {
		"foo": {True: foo0, False: foo1},
		"sustain": {True: sustain_on, False: sustain_off}
	}

	mappings = load_input_mappings("input.ini", name_to_midi, chords, midi_outputs, custom_actions)

	while True:
		for e in gamepad.read():
			btn = e.code.lower()
			pressed = bool(e.state)
			if btn in mappings:
				callbacks = mappings[btn]
				if pressed in callbacks and callbacks[pressed] is not None:
					mappings[btn][pressed]()
				print(btn, pressed)

if __name__ == "__main__":
	main()
