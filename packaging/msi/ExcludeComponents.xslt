<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
        xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
        xmlns:wix="http://schemas.microsoft.com/wix/2006/wi"
        xmlns="http://schemas.microsoft.com/wix/2006/wi"
        version="1.0"
        exclude-result-prefixes="xsl wix" >

    <xsl:output method="xml" indent="yes" omit-xml-declaration="yes"/>
    <xsl:strip-space elements="*"/>

    <!--
    Find all <Component> elements with <File> elements with Source="" attributes ending in ".exe" and tag it with the "ExeToRemove" key.

    <Component Id="cmpSYYKP6B1M7WSD5KLEQ7PZW4YLOPYG61L" Directory="INSTALLDIR" Guid="*">
        <File Id="filKUS7ZRMJ0AOKDU6ATYY6IRUSR2ECPDFO" KeyPath="yes" Source="!(wix.StagingAreaPath)\ProofOfPEqualsNP.exe" />
    </Component>

    Because WiX's Heat.exe only supports XSLT 1.0 and not XSLT 2.0 we cannot use `ends-with( haystack, needle )` (e.g. `ends-with( wix:File/@Source, '.exe' )`...
    ...but we can use this longer `substring` expression instead (see https://github.com/wixtoolset/issues/issues/5609 )
    -->
    <xsl:key
            name="UltiMaker_Cura_exe_ToRemove"
            match="wix:Component[ substring( wix:File/@Source, string-length( wix:File/@Source ) - 17 ) = 'UltiMaker-Cura.exe' ]"
            use="@Id"
    />
    <xsl:key
            name="CuraEngine_exe_ToRemove"
            match="wix:Component[ substring( wix:File/@Source, string-length( wix:File/@Source ) - 17 ) = 'CuraEngine.exe' ]"
            use="@Id"
    />

    <!-- By default, copy all elements and nodes into the output... -->
    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>

    <!-- ...but if the element has the "UltiMaker_Cura_exe_ToRemove" or "CuraEngine_exe_ToRemove" key then don't render anything (i.e. removing it from the output) -->
    <xsl:template match="*[ self::wix:Component or self::wix:ComponentRef ][ key( 'UltiMaker_Cura_exe_ToRemove', @Id ) ]"/>
    <xsl:template match="*[ self::wix:Component or self::wix:ComponentRef ][ key( 'CuraEngine_exe_ToRemove', @Id ) ]"/>
</xsl:stylesheet>