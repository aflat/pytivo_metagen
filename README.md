Many thanks to the authors of the original code that I butchered to make this work.

https://sourceforge.net/projects/pytivometathis/
and
https://github.com/KenV99/Tivo-Mind-Query

copy the pytivo_metagen.py.conf.default to pytivo_metagen.py.conf and add your 

tivo.com username
tivo.com password
tivo's tsn 

You can get the tsn (tivo service number) by logging into tivo.com and looking at your devices. 
Don't include the -'s It may work, I just haven't tested it, so feel free to try, and let me know it if works.

Also only tested on python 2.7. 

To use it, just run pytivo_metagen.py -f <a folder to scan>
