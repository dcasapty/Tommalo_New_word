#!/usr/bin/env bash
# Busca datos de otros negocios (D'CASA, Baby Caleb) que no deben estar en el repositorio de Tommalo. Se corre antes de
# cada push: scripts/revisar_datos_ajenos.sh. Sale con error (1) si encuentra algo de la lista DURA. La lista BLANDA
# (nombres de marca y de producto) solo avisa: puede aparecer en comentarios sobre la plantilla o en las listas de
# «prohibido» de las pruebas, pero nunca en contenido que ve el cliente.
#
# Esta lista no contiene los datos que busca (teléfonos, RUC): usa trozos que no dan la cifra completa.
set -uo pipefail
cd "$(dirname "$0")/.."
EXCLUIR=(--glob '!.git' --glob '!vendor/**' --glob '!node_modules' --glob '!scripts/revisar_datos_ajenos.sh' --glob '!docs/TOMMALO.md' --glob '!docs/superpowers/**' --glob '!docs/replicar/VALORES_DE_LA_EMPRESA.md')

# DURA: teléfonos (en sus formas con o sin separador), RUC, dirección, cuentas y dominios de otros negocios.
DURA='6026[ -]?19[ -]?19|6757[ -]?50[ -]?65|155779346|Libertadores|Discoteca Seven|juanarrietabusiness|babycalebpanama|babycaleb\.com|dcasapty\.com|dcasapty\.workers|sistemabk|vivimahechagarcia|info@dcasapty|ventas@dcasapty'
# BLANDA: nombres de marca y de producto de los otros negocios.
BLANDA="Baby ?Caleb|babycaleb|Nateen|Velvee|Dany Baby|Fular Moon|pañal|toallitas húmedas|D'CASA|D&#39;CASA|La Chorrera"

dura=$(rg -n -i "${EXCLUIR[@]}" -e "$DURA" . 2>/dev/null || true)
if [[ -n "$dura" ]]; then
  echo "✖ Datos de otros negocios (lista DURA):"
  echo "$dura" | cut -c1-200 | head -60
fi
blanda=$(rg -c -i "${EXCLUIR[@]}" -e "$BLANDA" . 2>/dev/null | sort -t: -k2 -rn | head -25 || true)
if [[ -n "$blanda" ]]; then
  echo "⚠ Nombres de marca o producto de otros negocios (lista BLANDA; revisar que no los vea el cliente):"
  echo "$blanda"
fi
# Claves o secretos con pinta de valor real (no se imprime el valor).
claves=$(rg -l -i "${EXCLUIR[@]}" -e '(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|xox[abp]-[A-Za-z0-9-]{10,})' . 2>/dev/null || true)
if [[ -n "$claves" ]]; then
  echo "✖ Posibles claves en: $claves"
  dura="$dura$claves"
fi
[[ -z "$dura" ]] || exit 1
echo "✔ Sin datos duros de otros negocios."
