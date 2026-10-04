#!/usr/bin/env bash
set -euo pipefail

ESTIMATE_FIELD="Estimate"
NO_ASSIGNEE="Sin asignar"
TEMPLATE='## Alcance


## Criterios de aceptación
- [ ] 
'

die() {
    echo "Error: $*" >&2
    exit 1
}

# select draws the menu on stderr, so only the chosen option reaches stdout.
choose() {
    local PS3="$1: "
    shift
    local option
    select option in "$@"; do
        if [[ -n "$option" ]]; then
            printf '%s\n' "$option"
            return 0
        fi
        echo "Opción inválida, elige un número de la lista." >&2
    done
    die "entrada cancelada."
}

[[ -t 0 ]] || die "este script es interactivo; ejecútalo desde una terminal."
command -v gh >/dev/null || die "GitHub CLI (gh) no está instalado."
gh auth status >/dev/null 2>&1 || die "gh no está autenticado; ejecuta 'gh auth login'."
gh repo view >/dev/null 2>&1 || die "no hay un repositorio de GitHub en este directorio."

labels_raw=$(gh label list --limit 200 --json name --jq '.[].name') \
    || die "no se pudieron obtener las labels del repositorio."
mapfile -t all_labels <<<"$labels_raw"

type_labels=()
for label in "${all_labels[@]}"; do
    if [[ -n "$label" ]]; then
        type_labels+=("$label")
    fi
done
(( ${#type_labels[@]} > 0 )) || die "el repositorio no tiene labels."

project_owner=""
project_number=""
project_id=""
field_id=""
if projects_raw=$(gh repo view --json owner,projectsV2 \
        --jq '.owner.login as $o | .projectsV2.Nodes[] | "\(.number)\t\($o)\t\(.title)"' \
        2>/dev/null) && [[ -n "$projects_raw" ]]; then
    mapfile -t projects <<<"$projects_raw"
    project_line="${projects[0]}"
    if (( ${#projects[@]} > 1 )); then
        echo
        echo "== Project =="
        project_line=$(choose "Project" "${projects[@]}")
    fi
    IFS=$'\t' read -r project_number project_owner _ <<<"$project_line"
    project_id=$(gh project view "$project_number" --owner "$project_owner" \
        --format json --jq '.id' 2>/dev/null) || project_id=""
    field_id=$(gh project field-list "$project_number" --owner "$project_owner" \
        --format json --jq ".fields[] | select(.name == \"$ESTIMATE_FIELD\") | .id" \
        2>/dev/null) || field_id=""
fi
if [[ -z "$project_id" ]]; then
    echo "Aviso: no se encontró un Project vinculado; la issue no se añadirá a ninguno." >&2
elif [[ -z "$field_id" ]]; then
    echo "Aviso: el Project no tiene el campo '$ESTIMATE_FIELD'; se omitirá la estimación." >&2
fi

echo
echo "== Type Issue =="
type_label=$(choose "Tipo" "${type_labels[@]}")

echo
title=""
while [[ -z "${title//[[:space:]]/}" ]]; do
    read -r -p "Título: " title || die "entrada cancelada."
done

echo
echo "== Asignación =="
if collaborators_raw=$(gh api "repos/{owner}/{repo}/collaborators" --paginate \
        --jq '.[].login' 2>/dev/null) && [[ -n "$collaborators_raw" ]]; then
    mapfile -t collaborators <<<"$collaborators_raw"
else
    echo "No se pudo obtener la lista de colaboradores; se ofrece solo @me." >&2
    collaborators=("@me")
fi
assignee=$(choose "Asignar a" "$NO_ASSIGNEE" "${collaborators[@]}")

estimate=""
if [[ -n "$field_id" ]]; then
    echo
    echo "== Tiempo estimado =="
    while true; do
        read -r -p "Estimación en días (ej. 0.5, 1, 2; vacío para omitir): " estimate \
            || die "entrada cancelada."
        estimate="${estimate//,/.}"
        if [[ -z "$estimate" || "$estimate" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
            break
        fi
        echo "Introduce un número, por ejemplo 1 o 0.5." >&2
    done
fi

body_file=$(mktemp --suffix=.md)
trap 'rm -f "$body_file"' EXIT
printf '%s' "$TEMPLATE" >"$body_file"
read -r -a editor_cmd <<<"${VISUAL:-${EDITOR:-nano}}"

while true; do
    "${editor_cmd[@]}" "$body_file"
    if [[ -n "$(tr -d '[:space:]' <"$body_file")" ]] \
        && ! diff -q -w -B <(printf '%s' "$TEMPLATE") "$body_file" >/dev/null; then
        break
    fi
    echo
    choice=$(choose "La descripción está vacía o sin cambios" "Volver a editar" "Cancelar")
    if [[ "$choice" == "Cancelar" ]]; then
        echo "Cancelado; no se creó ninguna issue."
        exit 0
    fi
done

echo
echo "== Resumen =="
echo "Tipo:        $type_label"
echo "Título:      $title"
echo "Asignado:    $assignee"
echo "Project:     ${project_number:+#$project_number ($project_owner)}"
echo "Estimación:  ${estimate:-Sin estimación}${estimate:+ días}"
echo "Descripción:"
head -n 8 "$body_file" | sed 's/^/    /'
echo

read -r -p "¿Crear la issue? [s/N]: " confirm || confirm=""
if [[ ! "$confirm" =~ ^[sS] ]]; then
    echo "Cancelado; no se creó ninguna issue."
    exit 0
fi

args=(--title "$title" --body-file "$body_file" --label "$type_label")
if [[ "$assignee" != "$NO_ASSIGNEE" ]]; then
    args+=(--assignee "$assignee")
fi

issue_url=$(gh issue create "${args[@]}")
echo "Issue creada: $issue_url"

[[ -n "$project_id" ]] || exit 0

# item-add returns the existing item if the Project already auto-added the issue.
if ! item_id=$(gh project item-add "$project_number" --owner "$project_owner" \
        --url "$issue_url" --format json --jq '.id'); then
    die "la issue se creó pero no se pudo añadir al Project #$project_number."
fi
echo "Añadida al Project #$project_number."

if [[ -n "$estimate" ]]; then
    gh project item-edit --id "$item_id" --project-id "$project_id" \
        --field-id "$field_id" --number "$estimate" >/dev/null \
        || die "la issue está en el Project pero no se pudo guardar la estimación."
    echo "$ESTIMATE_FIELD = $estimate"
fi