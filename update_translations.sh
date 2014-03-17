#/bin/sh
xgettext --language=Python --copyright-holder='David Braam' --keyword=_ --output=resources/locale/Cura.pot --from-code=UTF-8 `find Cura -name "*.py"`

for LANG in `ls resources/locale`; do
	if [ -e resources/locale/$LANG/LC_MESSAGES/Cura.po ]; then
		msgmerge -U resources/locale/$LANG/LC_MESSAGES/Cura.po resources/locale/Cura.pot
		msgfmt resources/locale/$LANG/LC_MESSAGES/Cura.po --output-file resources/locale/$LANG/LC_MESSAGES/Cura.mo
	fi
done
