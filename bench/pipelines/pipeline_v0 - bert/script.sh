#!/bin/bash

# Script avanzado para recuperar archivos JSON del historial de Git
# Busca en: nombres de carpetas, nombres de archivos, y contenido de JSONs

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Directorio de recuperación
RECOVERY_DIR="plot_recover"

# Patrones a buscar (case-insensitive)
PATTERNS=("medgemma" "jonsnow" "sakura" "openbio")

# Variables para progreso
total_commits=0
current_commit=0
files_found=0
files_recovered=0

# Función para mostrar barra de progreso
show_progress() {
    local current=$1
    local total=$2
    local percent=$((current * 100 / total))
    local bars=$((percent / 2))
    
    printf "\r[${CYAN}"
    for ((i=0; i<bars; i++)); do printf "█"; done
    for ((i=bars; i<50; i++)); do printf "░"; done
    printf "${NC}] ${percent}%% (${current}/${total} commits)"
}

# Función para verificar patrones (case-insensitive)
matches_pattern() {
    local text=$1
    local text_lower=$(echo "$text" | tr '[:upper:]' '[:lower:]')
    
    for pattern in "${PATTERNS[@]}"; do
        pattern_lower=$(echo "$pattern" | tr '[:upper:]' '[:lower:]')
        if [[ "$text_lower" == *"$pattern_lower"* ]]; then
            return 0
        fi
    done
    return 1
}

# Verificar que estamos en un repo Git
ROOT_DIR=$(git rev-parse --show-toplevel 2>/dev/null)
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: No estás en un repositorio Git${NC}"
    exit 1
fi

echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}    RECUPERADOR AVANZADO DE JSON - GIT HISTORY${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "\n${YELLOW}Configuración:${NC}"
echo -e "  • Repositorio: ${CYAN}$ROOT_DIR${NC}"
echo -e "  • Patrones buscados: ${CYAN}${PATTERNS[*]}${NC}"
echo -e "  • Directorio destino: ${CYAN}$ROOT_DIR/$RECOVERY_DIR${NC}"

# Crear carpeta de recuperación
FULL_RECOVERY_PATH="$ROOT_DIR/$RECOVERY_DIR"
mkdir -p "$FULL_RECOVERY_PATH"

# Crear archivo de log detallado
LOG_FILE="$FULL_RECOVERY_PATH/recovery_log.txt"
echo "Recovery Log - $(date)" > "$LOG_FILE"
echo "Patterns: ${PATTERNS[*]}" >> "$LOG_FILE"
echo "=================" >> "$LOG_FILE"

# Obtener total de commits para la barra de progreso
echo -e "\n${YELLOW}Calculando tamaño del historial...${NC}"
total_commits=$(git rev-list --all --count)
echo -e "Total de commits a analizar: ${CYAN}$total_commits${NC}"

# Arrays para almacenar archivos encontrados
declare -A found_files
declare -A file_commits

echo -e "\n${YELLOW}FASE 1: Escaneando todo el historial de Git...${NC}"
echo -e "${BLUE}Buscando en: nombres de carpetas, nombres de archivos y contenido${NC}\n"

# Obtener todos los commits
git rev-list --all | while read commit; do
    ((current_commit++))
    show_progress $current_commit $total_commits
    
    # Buscar archivos JSON en este commit
    git ls-tree -r "$commit" --name-only | grep '\.json$' | while read filepath; do
        
        # CASO 1: El nombre del archivo JSON contiene el patrón
        if matches_pattern "$(basename "$filepath")"; then
            found_files["$filepath"]=1
            file_commits["$filepath"]="$commit"
            echo -e "\n${GREEN}[Nombre archivo]${NC} $filepath @ ${commit:0:7}" | tee -a "$LOG_FILE"
            ((files_found++))
            continue
        fi
        
        # CASO 2: La carpeta que contiene el JSON tiene el patrón
        dir_path=$(dirname "$filepath")
        if matches_pattern "$dir_path"; then
            found_files["$filepath"]=1
            file_commits["$filepath"]="$commit"
            echo -e "\n${GREEN}[Carpeta]${NC} $filepath @ ${commit:0:7}" | tee -a "$LOG_FILE"
            ((files_found++))
            continue
        fi
        
        # CASO 3: El contenido del JSON contiene el patrón
        # Esto es más lento, pero encuentra JSONs por contenido
        content=$(git show "$commit:$filepath" 2>/dev/null | tr '[:upper:]' '[:lower:]')
        if [ ! -z "$content" ]; then
            for pattern in "${PATTERNS[@]}"; do
                pattern_lower=$(echo "$pattern" | tr '[:upper:]' '[:lower:]')
                if [[ "$content" == *"$pattern_lower"* ]]; then
                    found_files["$filepath"]=1
                    file_commits["$filepath"]="$commit"
                    echo -e "\n${BLUE}[Contenido]${NC} $filepath @ ${commit:0:7} (contiene: $pattern)" | tee -a "$LOG_FILE"
                    ((files_found++))
                    break
                fi
            done
        fi
    done
done

echo -e "\n\n${YELLOW}FASE 2: Recuperando archivos encontrados...${NC}"
echo -e "Archivos únicos encontrados: ${CYAN}${#found_files[@]}${NC}\n"

# Recuperar cada archivo encontrado
file_count=0
for filepath in "${!found_files[@]}"; do
    ((file_count++))
    echo -e "\n${YELLOW}[$file_count/${#found_files[@]}]${NC} Procesando: $filepath"
    
    # Buscar el mejor commit para recuperar el archivo
    # (el más reciente donde existe y no está vacío)
    best_commit=""
    git log --all --pretty=format:"%H" -- "$filepath" | while read commit; do
        if git ls-tree -r "$commit" --name-only | grep -q "^${filepath}$"; then
            # Verificar que el archivo no esté vacío
            size=$(git cat-file -s "$commit:$filepath" 2>/dev/null || echo "0")
            if [ "$size" -gt 0 ]; then
                best_commit=$commit
                break
            fi
        fi
    done
    
    if [ ! -z "$best_commit" ]; then
        # Crear nombre único basado en la ruta completa
        # Reemplazar / por _ para evitar problemas
        safe_path=$(echo "$filepath" | sed 's/\//_/g')
        unique_name="${best_commit:0:7}_${safe_path}"
        
        # Recuperar el archivo
        git show "$best_commit:$filepath" > "$FULL_RECOVERY_PATH/$unique_name" 2>/dev/null
        
        if [ $? -eq 0 ] && [ -s "$FULL_RECOVERY_PATH/$unique_name" ]; then
            echo -e "  ${GREEN}✓ Recuperado como:${NC} $unique_name"
            echo "  ✓ $filepath -> $unique_name" >> "$LOG_FILE"
            ((files_recovered++))
            
            # Guardar metadatos
            echo "{" > "$FULL_RECOVERY_PATH/${unique_name}.meta"
            echo "  \"original_path\": \"$filepath\"," >> "$FULL_RECOVERY_PATH/${unique_name}.meta"
            echo "  \"commit\": \"$best_commit\"," >> "$FULL_RECOVERY_PATH/${unique_name}.meta"
            echo "  \"commit_date\": \"$(git show -s --format=%ci $best_commit)\"," >> "$FULL_RECOVERY_PATH/${unique_name}.meta"
            echo "  \"recovery_date\": \"$(date -Iseconds)\"" >> "$FULL_RECOVERY_PATH/${unique_name}.meta"
            echo "}" >> "$FULL_RECOVERY_PATH/${unique_name}.meta"
        else
            echo -e "  ${RED}✗ Error al recuperar${NC}"
            rm -f "$FULL_RECOVERY_PATH/$unique_name"
        fi
    else
        echo -e "  ${RED}✗ No se encontró versión válida${NC}"
    fi
done

# También buscar en el directorio actual
echo -e "\n${YELLOW}FASE 3: Buscando en el directorio actual...${NC}"
current_files=0

find . -name "*.json" -type f 2>/dev/null | while read filepath; do
    # Aplicar los mismos criterios de búsqueda
    found=false
    reason=""
    
    # Check nombre archivo
    if matches_pattern "$(basename "$filepath")"; then
        found=true
        reason="nombre"
    # Check carpeta
    elif matches_pattern "$(dirname "$filepath")"; then
        found=true
        reason="carpeta"
    # Check contenido
    else
        content=$(cat "$filepath" 2>/dev/null | tr '[:upper:]' '[:lower:]')
        for pattern in "${PATTERNS[@]}"; do
            pattern_lower=$(echo "$pattern" | tr '[:upper:]' '[:lower:]')
            if [[ "$content" == *"$pattern_lower"* ]]; then
                found=true
                reason="contenido:$pattern"
                break
            fi
        done
    fi
    
    if [ "$found" = true ]; then
        echo -e "${GREEN}[Actual - $reason]${NC} $filepath"
        safe_path=$(echo "$filepath" | sed 's/\//_/g')
        unique_name="current_${safe_path}"
        
        cp "$filepath" "$FULL_RECOVERY_PATH/$unique_name" 2>/dev/null
        if [ $? -eq 0 ]; then
            ((current_files++))
            echo "  ✓ Actual: $filepath -> $unique_name" >> "$LOG_FILE"
        fi
    fi
done

# Resumen final
echo -e "\n${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                    RESUMEN FINAL${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "  • Commits analizados: ${CYAN}$total_commits${NC}"
echo -e "  • Archivos encontrados en historial: ${CYAN}$files_found${NC}"
echo -e "  • Archivos recuperados del historial: ${CYAN}$files_recovered${NC}"
echo -e "  • Archivos del directorio actual: ${CYAN}$current_files${NC}"
echo -e "  • ${YELLOW}Total recuperado:${NC} ${GREEN}$((files_recovered + current_files))${NC}"
echo -e "\n  • Ubicación: ${CYAN}$FULL_RECOVERY_PATH${NC}"
echo -e "  • Log detallado: ${CYAN}$LOG_FILE${NC}"

# Mostrar archivos recuperados
if [ -d "$FULL_RECOVERY_PATH" ] && [ "$(ls -A "$FULL_RECOVERY_PATH" | grep -v "\.meta$" | grep -v "log\.txt$")" ]; then
    echo -e "\n${YELLOW}Archivos recuperados (mostrando primeros 10):${NC}"
    ls -lah "$FULL_RECOVERY_PATH" | grep -v "\.meta$" | grep -v "log\.txt$" | head -n 11
    
    total_files=$(ls -1 "$FULL_RECOVERY_PATH" | grep -v "\.meta$" | grep -v "log\.txt$" | wc -l)
    if [ $total_files -gt 10 ]; then
        echo -e "... y $((total_files - 10)) archivos más"
    fi
else
    echo -e "\n${RED}No se recuperaron archivos${NC}"
fi

echo -e "\n${CYAN}Tip: Los archivos .meta contienen información sobre el origen de cada archivo${NC}"
echo -e "${CYAN}Tip: Revisa recovery_log.txt para ver el detalle completo${NC}\n"