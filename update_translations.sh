#/bin/sh
xgettext --language=Python --copyright-holder='David Braam' --keyword=_ --output=Cura/resources/locale/Cura.pot --from-code=UTF-8 `find Cura -name "*.py"`

for LANG in `ls Cura/resources/locale`; do
	if [ -e Cura/resources/locale/$LANG/LC_MESSAGES/Cura.po ]; then
		msgmerge -U Cura/resources/locale/$LANG/LC_MESSAGES/Cura.po Cura/resources/locale/Cura.pot
		msgfmt Cura/resources/locale/$LANG/LC_MESSAGES/Cura.po --output-file Cura/resources/locale/$LANG/LC_MESSAGES/Cura.mo
	fi
done
