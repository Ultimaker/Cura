#! /bin/bash

default_i18n_dir="resources/i18n"
i18n_dir=${1:-$default_i18n_dir}

for language_dir in "$i18n_dir"/*; do
    if [[ -d "$language_dir" ]]; then
	    git rm $language_dir/uranium.po
	    git rm $language_dir/gradual_flow_settings.def.json.po
        for language_file in "$language_dir"/*.po; do
            echo "Cleaning file $language_file"
            sed -i "/#, fuzzy/d" "$language_file"
            sed -i "/#, python-brace-format/d" "$language_file"
            sed -i "/#, python-format/d" "$language_file"
            git add "$language_file"
        done
    fi
done

git rm $default_i18n_dir/uranium.po
git rm cura.po
git rm uranium.po


echo "##########################################"
echo "################# Moving to Uranium folder"
echo "##########################################"
cd "../Uranium"

for language_dir in "$i18n_dir"/*; do
    if [[ -d "$language_dir" ]]; then
	    git rm $language_dir/cura.po
	    git rm $language_dir/fdmprinter.def.json.po
	    git rm $language_dir/fdmextruder.def.json.po
	    git rm $language_dir/gradual_flow_settings.def.json.po
        for language_file in "$language_dir"/*.po; do
            echo "Cleaning file $language_file"
            sed -i "/#, fuzzy/d" "$language_file"
            sed -i "/#, python-brace-format/d" "$language_file"
            sed -i "/#, python-format/d" "$language_file"
            git add "$language_file"
        done
    fi
done

git rm $default_i18n_dir/cura.po
git rm cura.po
git rm uranium.po
