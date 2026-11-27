/**
 * Las páginas que sirve el borde por su cuenta (mientras Odoo arranca y la de la puerta del equipo) llevan la marca
 * Tommalo (docs/MARCA_TOMMALO.md, 2026-11-19): crema, letra navy, titulares como frase, el naranja solo de
 * relleno con letra navy encima, y nada del azul, del amarillo ni de las letras de D'CASA.
 */
import { describe, expect, it } from "vitest";
import { respuestaArrancando } from "../src/arranque";
import { respuestaPuertaIncompleta, respuestaPuertaNoAbre } from "../src/puerta_aviso";

const DE_DCASA = /1340B1|FED00F|0B2160|0E2A6B|Anton|Oswald|text-transform:uppercase;letter-spacing:\.0/i;

function marcaTommalo(html: string) {
  expect(html).toContain("background:#FAFAFA");
  expect(html).toContain("color:#262626");
  expect(html).toContain("font-family:Montserrat");
  // El botón: naranja de relleno con letra navy, en pastilla.
  expect(html).toMatch(/background:#D4D4D4;color:#262626;font-weight:700/);
  expect(html).toContain("border-radius:999px");
  // El naranja nunca va de letra: «color:#D4D4D4» no aparece.
  expect(html).not.toMatch(/(^|[;{\s])color:#D4D4D4/i);
  expect(html).not.toMatch(DE_DCASA);
}

describe("marca Tommalo en las páginas del borde", () => {
  it("la de «estamos abriendo la tienda»", async () => {
    const res = respuestaArrancando(new Request("https://tommalo.example/", { headers: { Accept: "text/html" } }));
    marcaTommalo(await res.text());
  });

  it("la de la puerta del equipo cuando no abre", async () => {
    const res = respuestaPuertaNoAbre(
      new Request("https://tommalo.example/master"),
      { motivo: "sin token" },
      { ruta: "/master", modo: "1", entorno: "staging", ahora: () => 0 },
    );
    const html = await res.text();
    marcaTommalo(html);
    expect(html).toContain("<title>Tommalo · Acceso del equipo</title>");
  });

  it("la de la puerta incompleta", async () => {
    const res = respuestaPuertaIncompleta(
      new Request("https://tommalo.example/master"),
      { estado: "incompleta", modo: "0", faltan: ["DCASA_ACCESS_AUD"], ruta: "/master" },
      { entorno: "staging", ahora: () => 0 },
    );
    const html = await res.text();
    expect(html).toContain("background:#FAFAFA");
    expect(html).not.toMatch(DE_DCASA);
  });
});
