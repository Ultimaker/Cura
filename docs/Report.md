
# Reporting Issues

Please attach the following information in case <br>
you want to report crashing or similar issues.

<br>

## DxDiag

### ![Badge Windows]

The log as produced by **dxdiag**.

<kbd>  start  </kbd>  »  <kbd>  run  </kbd>  »  <kbd>  dxdiag  </kbd>  »  <kbd>  save output  </kbd>

<br>
<br>

## Cura GUI Log

If the Cura user interface still starts, you can also <br>
reach these directories from the application menu:

<kbd>  Help  </kbd>  »  <kbd>  Show settings folder  </kbd>

<br>

### ![Badge Windows]

```
%APPDATA%\cura\<Ｃｕｒａ Ｖｅｒｓｉｏｎ>\cura.log
```

or

```
C:\Users\<your username>\AppData\Roaming\cura\<Ｃｕｒａ Ｖｅｒｓｉｏｎ>\cura.log
```

<br>

### ![Badge Linux]

```
~/.local/share/cura/<Ｃｕｒａ Ｖｅｒｓｉｏｎ>/cura.log
```

<br>

### ![Badge MacOS]

```
~/Library/Application Support/cura/<Ｃｕｒａ Ｖｅｒｓｉｏｎ>/cura.log
```

<br>
<br>

## Alternative

An alternative is to install the **[ExtensiveSupportLogging]** <br>
plugin this creates a zip folder of the relevant log files.

If you're experiencing performance issues, we might ask <br>
you to connect the CPU profiler in this plugin and attach <br>
the collected data to your support ticket. 

<br>


<!----------------------------------------------------------------------------->

[ExtensiveSupportLogging]: https://marketplace.ultimaker.com/app/cura/plugins/UltimakerPackages/ExtensiveSupportLogging


<!---------------------------------[ Badges ]---------------------------------->

[Badge Windows]: https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logoColor=white&logo=Windows
[Badge Linux]: https://img.shields.io/badge/Linux-00A95C?style=for-the-badge&logoColor=white&logo=Linux
[Badge MacOS]: https://img.shields.io/badge/MacOS-403C3D?style=for-the-badge&logoColor=white&logo=MacOS
