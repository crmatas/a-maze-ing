OWNER=$(gh repo view --json owner --jq .owner.login)

mapfile -t PROJECTS < <(gh project list --owner "$OWNER" --format json --jq '.projects[].title')
if [ "${#PROJECTS[@]}" -eq 1 ]; then
    PROJECT=${PROJECTS[0]}
else
    select PROJECT in "${PROJECTS[@]}"; do break; done
fi

gh pr create -p "$PROJECT" --base develop --fill