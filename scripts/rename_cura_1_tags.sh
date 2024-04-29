#Renames tags that were for Legacy Cura to a newer versioning system.
#Those Cura versions used tags based on the year of release.
#We'd like to rename them to be "Cura 1" and have the original version number as sub-version-numbers.
#So Cura 14.04 becomes Cura 1.14.04.

for i in $(git tag -l)
do
    if [[ $i =~ ^1[2-5]\.[0-9][0-9] ]]; then #E.g. 12.04 or 15.06. Note that there is no end-match so anything that starts with this matches.
        echo "Renaming tag $i to 1.$i";
        git tag 1.$i $i; #Create new tag (1.x instead of x).
        git tag -d $i; #Delete old tag.
        git push origin 1.$i :$i #Rename the tag remotely too.
    fi
done
