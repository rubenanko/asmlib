nasm -f elf64 $1 -o $1.o
ld -o $2 $1.o


#!/bin/bash

# Vérifie qu'il y a au moins 2 arguments
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 fichier1.asm fichier2.asm ... executable"
    exit 1
fi

# Le dernier argument est le nom de l'exécutable
exe="${@: -1}"

# Tous les autres sont des sources
sources=("${@:1:$#-1}")

# Tableau des objets
objects=()

# Assemble chaque source
for src in "${sources[@]}"; do
    obj="${src%.asm}.o"
    echo nasm -f elf64 "$src" -o "$obj"
    objects+=("$obj")
done

# Lie tous les objets
echo ld -o "$exe" "${objects[@]}" 