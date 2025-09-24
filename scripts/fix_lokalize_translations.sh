#! /bin/bash

default_i18n_dir="resources/i18n"
i18n_dir=${1:-$default_i18n_dir}

for language_dir in "$i18n_dir"/*; do
    if [[ -d "$language_dir" ]]; then
        for language_file in "$language_dir"/*.po; do
	    echo "Cleaning file $language_file"
            sed -i "/#, fuzzy/d" "$language_file"
	    sed -i "/#, python-brace-format/d" "$language_file"
	    sed -i "/#, python-format/d" "$language_file"
        done
    fi
done
