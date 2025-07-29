\documentclass[11pt, a4paper]{article}

% --- PAQUETES ---
\usepackage[utf8]{inputenc}
\usepackage[spanish]{babel}
\usepackage{geometry}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{fancyhdr}
\usepackage{amsmath}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{tabularx}
\usepackage{titlesec}
\usepackage[font={small,it,color=graytext}, labelsep=period, justification=centering]{caption}
\usepackage{float}
\usepackage{appendix} % Paquete para los anexos
\usepackage{tikz}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning}
\usepackage{verbatim} % Para incluir código de prompts
\usepackage{makecell}

% --- CONFIGURACIÓN DE PÁGINA Y ESTILO ---
\geometry{a4paper, margin=2.5cm}
\setlength{\headheight}{14.5pt} % <-- CORRECCIÓN: Aumentar el espacio para el encabezado

\definecolor{primarycolor}{RGB}{0, 51, 102} % Azul oscuro corporativo
\definecolor{graytext}{RGB}{80, 80, 80}

\hypersetup{
    colorlinks=true,
    linkcolor=primarycolor,
    urlcolor=primarycolor,
    citecolor=primarycolor
}

\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\nouppercase{\leftmark}}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0pt}
\fancypagestyle{plain}{\fancyhf{}}

% --- FORMATO DE TÍTULOS (CORREGIDO PARA TOC) ---
\titleformat{\section}
  {\normalfont\Large\bfseries\color{primarycolor}}
  {\thesection.}{1em}{}
\titlespacing*{\section}{0pt}{3.5ex plus 1ex minus .2ex}{2.3ex plus .2ex}

\titleformat{\subsection}
  {\normalfont\large\bfseries\color{graytext}}
  {\thesubsection}{1em}{}
\titlespacing*{\subsection}{0pt}{3.25ex plus 1ex minus .2ex}{1.5ex plus .2ex}

\titleformat{\subsubsection}
  {\normalfont\normalsize\bfseries}
  {\thesubsubsection}{1em}{}
\titlespacing*{\subsubsection}{0pt}{3.25ex plus 1ex minus .2ex}{1.5ex plus .2ex}

% Definición de colores para el diagrama
\definecolor{snomed}{RGB}{217, 234, 211} % Verde claro
\definecolor{icd}{RGB}{252, 229, 205}    % Naranja claro
\definecolor{bert}{RGB}{214, 234, 248}   % Azul claro
\definecolor{llm}{RGB}{235, 222, 240}    % Morado claro

\tikzset{
    proc/.style={
        rectangle, 
        rounded corners, 
        draw=black, 
        thick,
        minimum height=1.2cm, 
        minimum width=2.8cm,
        text centered,
        font=\small,
        align=center % <-- CORRECCIÓN: Permite saltos de línea robustos con \\
    },
    dec/.style={
        diamond,
        draw=black,
        thick,
        aspect=1.8,
        minimum size=1.5cm,
        text centered,
        font=\small
    },
    out/.style={
        ellipse,
        draw=primarycolor,
        thick,
        minimum height=1cm,
        minimum width=2cm,
        text centered,
        font=\small\bfseries
    },
    line/.style={
        -Stealth, % Punta de flecha moderna
        thick,
        draw=graytext
    }
}

% --- DOCUMENTO ---
\begin{document}

% --- PÁGINA DE TÍTULO ---
% ---------- PORTADA WHITE PAPER ----------------------------------
\begin{titlepage}
    \centering
    
    % Espacio flexible al inicio
    \vspace*{\fill}
    
    % Logo corporativo
    \includegraphics[height=2.5cm]{logo-29.webp}
    
    \vspace{1.5cm}
    
    % Título principal con menos espacio después
    {\Huge\bfseries\color{primarycolor}
    Formalización métrica del juicio clínico en sistemas LLM de diagnóstico diferencial\par}
    
    \vspace{0.5cm} % Reducido de 0.8cm
    
    % Subtítulo
    {\Large\color{graytext}
    Un marco de evaluación híbrido ontológico-semántico para superar la convergencia artificial de rendimiento\par}
    
    % Espacio flexible que empuja el contenido hacia arriba y abajo
    \vspace{\fill}
    
    % Información de autores
    \begin{flushleft}
    \large
    \textbf{Autores}\\[0.3em]
    \normalsize
    Yago Mendoza\\
    Javier Logroño\\
    Carlos Bermejo
    \end{flushleft}
    
    \vspace{1cm}
    
    % Línea divisoria
    \rule{\textwidth}{0.5pt}
    
    \vspace{0.5cm}
    
    % Metadatos al pie
    \begin{minipage}[t]{0.45\textwidth}
        \begin{flushleft}
        \textbf{Foundation 29}\\
        \today
        \end{flushleft}
    \end{minipage}
    \hfill
    \begin{minipage}[t]{0.45\textwidth}
        \begin{flushright}
        \textbf{Versión 2.1}\\
        White Paper Técnico
        \end{flushright}
    \end{minipage}
    
    % Espacio flexible al final
    \vspace*{\fill}
    
\end{titlepage}

% ---------- FIN PORTADA ------------------------------------------


\newpage

\begin{center}
    {\Large \textbf{Resumen}}\\[1em]  % \LARGE hace el texto más grande, [1em] agrega espacio debajo
\end{center}

Este informe detalla la evolución metodológica y los hallazgos en la evaluación de cuatro modelos de lenguaje de OpenAI —\textbf{GPT-4o, o1, o3 y o3-pro}— en un benchmark de \textbf{450 casos clínicos pediátricos}. El estudio partió de la premisa de que los enfoques de evaluación simples generan resultados engañosos. Se demostró que un pipeline basado en códigos (\textbf{PV2}: \textbf{ICD-10} + \textbf{BERT}) penalizaba la especificidad clínica (la ``\textbf{paradoja del especialista castigado}''), mientras que un juez-\textbf{LLM} (\textbf{PV3}) enmascaraba las diferencias de rendimiento al premiar la plausibilidad sobre la precisión, provocando una \textbf{saturación de la tarea}.

Para superar estas limitaciones, se desarrolló \textbf{PV4}, un \textbf{pipeline jerárquico} que integra la objetividad de las ontologías médicas (\textbf{SNOMED, ICD-10}) con el juicio semántico contextual (\textbf{BERT, LLM}). La innovación clave de \textbf{PV4} es el uso de la \textbf{posición del diagnóstico correcto en la lista diferencial} como métrica principal, evaluando así la capacidad de \textbf{priorización clínica} del modelo.

Esta nueva metodología logró romper la aparente convergencia de los modelos, revelando una \textbf{clara jerarquía de rendimiento}. El modelo \textbf{o3} emergió como el más fiable y con la mejor capacidad de priorización (posición promedio de \textbf{1,47} y \textbf{311} aciertos en primera posición). En contraste, \textbf{o3-pro}, aunque alcanzó la tasa de acierto bruta marginalmente más alta (\textbf{96,4\%}), lo hizo a costa de una priorización inferior (posición promedio de \textbf{1,60}) y una mayor dependencia de los evaluadores semánticos. Adicionalmente, el análisis de \textbf{prompts} confirmó que \textbf{exigir un razonamiento explícito} —como listar síntomas a favor y en contra— es la estrategia más eficaz para optimizar la calidad del diagnóstico, superando tanto a los formatos simples como a los sobrecargados.


\vspace{2cm}

\newpage

\tableofcontents
\newpage

\section{Planteamiento del problema de evaluación}

La validación de sistemas de IA para el soporte al diagnóstico clínico representa uno de los desafíos metodológicos más complejos y estratégicamente relevantes en la medicina contemporánea. No se trata simplemente de verificar si una IA acierta en su diagnóstico, sino de evaluar la calidad, robustez y relevancia clínica de su razonamiento. Esta distinción es crucial: en el contexto real de atención médica, una hipótesis diagnóstica que suena plausible pero no es precisa puede comprometer tanto la seguridad del paciente como la confianza del profesional.

Como fundación dedicada al desarrollo ético y riguroso de herramientas diagnósticas basadas en IA, nuestro objetivo es establecer un marco de evaluación que supere las métricas superficiales y permita discernir con claridad el rendimiento diferencial entre modelos de distintas generaciones. Esta evaluación no debe limitarse a contar aciertos, sino que debe capturar las dimensiones más profundas del juicio clínico, incluyendo la priorización, la precisión terminológica y la coherencia semántica. Este informe documenta el proceso iterativo que hemos seguido para construir dicho marco cubriendo esos tres aspectos.

Partimos de una premisa de escepticismo científico: toda metodología de evaluación introduce sesgos y artefactos. Por tanto, nuestro trabajo no ha sido solo aplicar métricas, sino también interrogarlas, tensionarlas y rediseñarlas. Cada fase de nuestro pipeline nos ha permitido ver una parte distinta del problema —desde la rigidez de los sistemas de codificación hasta la excesiva generosidad de los evaluadores holísticos basados en \textbf{LLMs}— y, en ese recorrido, hemos aprendido tanto sobre los modelos como sobre nuestras propias herramientas de medición.

Más allá de evaluar un conjunto de modelos en un momento concreto, este documento busca sentar las bases para una evaluación clínicamente significativa y transparente.

\section{Composición del entorno de pruebas}
Para llevar a cabo una evaluación rigurosa, es indispensable contar con un entorno de pruebas que sea representativo y desafiante. El punto de partida es un conjunto agregado de 9.677 casos médicos provenientes de siete fuentes distintas, que incluyen recursos educativos (MedBullet, MedQA), bases de datos de enfermedades raras (RAMEDIS, Rare Synthetic), casos de urgencias (URGTorre) y otros de carácter especializado (Ukrainian, NEJM).

Si bien a lo largo del proyecto se probaron varias combinaciones de casos en función de los trade-offs de coste y tiempo en diversos pipelines, especialmente para pruebas rápidas o confirmaciones de hipótesis menores, para las evaluaciones definitivas de ranking se utilizó el dataset más equilibrado que se encontró. Entre todos los subconjuntos posibles derivados del corpus de 9.677 casos, este conjunto de \textbf{450 casos clínicos} fue seleccionado por un algoritmo de diversidad optimizada que maximiza la cobertura diagnóstica y minimiza la redundancia clínica, logrando el mejor equilibrio entre representatividad, complejidad y eficiencia computacional. Una visualización detallada de este proceso de extracción, transformación y carga (ETL) se encuentra en el \textbf{Anexo A}.

\subsection{Diversidad del dataset final}
La construcción del dataset final de \textbf{450 casos clínicos} se realizó mediante un proceso de \textbf{curación algorítmica por fases}, un enfoque diseñado para superar los sesgos de representatividad y la redundancia inherentes al muestreo aleatorio. El objetivo no era crear una muestra estadísticamente representativa de la prevalencia de enfermedades, sino construir un \textit{benchmark} de alta exigencia, optimizado para discriminar el rendimiento de los modelos. La lógica operativa fue la siguiente:

\begin{enumerate}[leftmargin=*, label=\textbf{Fase \arabic*:}]
    \item \textbf{Establecimiento de un núcleo estratificado:} El proceso comienza garantizando la inclusión de un conjunto de casos de fuentes consideradas estratégicas. Se preasigna una cuota mínima o total para datasets de alta relevancia, como los de enfermedades raras (RAMEDIS) o complejidad diagnóstica (NEJM). Esta estratificación inicial asegura la presencia de escenarios de baja prevalencia pero alto valor informativo, que un muestreo aleatorio simple probablemente omitiría.

    \item \textbf{Llenado por optimización de la diversidad marginal:} Una vez asegurado el núcleo, el algoritmo completa el dataset de forma iterativa. En cada paso, en lugar de una selección aleatoria, se implementa una \textbf{heurística de puntuación ponderada} para evaluar a todos los candidatos restantes. Se selecciona aquel caso que ofrezca el \textbf{máximo valor marginal}, es decir, el que más contribuya a la diversidad y complejidad del conjunto ya formado. Dicha heurística pondera simultáneamente varios ejes de calidad:
        \begin{itemize}[nosep]
            \item \textbf{Maximización de la cobertura taxonómica:} La máxima ponderación se asigna a los casos que introducen un \textbf{capítulo ICD-10} no representado. Este criterio fuerza al dataset a cubrir un espectro amplio de dominios médicos.
            \item \textbf{Minimización de la redundancia nosológica:} Se bonifica la inclusión de diagnósticos con códigos ICD-10 específicos aún no presentes, evitando la saturación del \textit{benchmark} con patologías comunes.
            \item \textbf{Balance de fuentes de origen:} Se aplica un factor de corrección que favorece a los casos de fuentes subrepresentadas, mitigando el riesgo de que el dataset final esté dominado por las características de una única colección masiva.
            \item \textbf{Priorización de la complejidad:} Se premian explícitamente los casos con mayores índices de complejidad y severidad\footnote{Índice entendido no como la gravedad clínica para el paciente, sino como una aproximación a la dificultad diagnóstica, generada mediante un modelo. No se utiliza como métrica de rendimiento directa, pero sí como dimensión auxiliar para la visualización de resultados.} para asegurar que el \textit{benchmark} contenga una proporción significativa de escenarios diagnósticos no triviales.
        \end{itemize}
\end{enumerate}

El resultado es un conjunto de pruebas que, a diferencia de una muestra aleatoria, está intencionadamente sesgado hacia la diversidad y la dificultad. Este diseño lo convierte en un \textit{benchmark} con mayor poder discriminativo, capaz de tensionar y diferenciar de manera más fiable las capacidades de razonamiento clínico de los distintos modelos. Una visualización detallada de este proceso de extracción, transformación y carga (ETL) se encuentra en el \textbf{Anexo A}.

\begin{figure}[H]
    \centering
    \includegraphics[width=1.0\linewidth]{imgs/00_all_450_diversity_visualized.jpeg}
    \caption{Distribución de los 450 casos clínicos por capítulos de la codificación \textbf{ICD-10}. El eje X muestra los 21 capítulos del CDX, una clasificación clínica de alto nivel; su función es únicamente referencial dentro del patrón general de resultados.}
    \label{fig:diversity}
\end{figure}

Cada uno de los 450 casos del dataset fue extraído de un universo clínico mayor (9.600 casos), transformado mediante un \textbf{pipeline de ETL multietapa} documentado dentro del módulo \texttt{data29}. Este proceso incluyó: extracción desde fuentes médicas heterogéneas, limpieza semántica, codificación estandarizada (ICD-10, SNOMED CT), enriquecimiento con metadatos, deduplicación y validación de calidad.

En este contexto, la \textbf{validez del diagnóstico de referencia (GDX)} de cada caso —es decir, la hipótesis clínica que se considera “verdadera” a efectos de evaluación— no fue asumida directamente ni generada ad hoc, sino construida como una verdad clínica operacional. Aunque no se aplicó una revisión manual caso por caso por parte de un panel externo, el proceso incluyó validaciones cruzadas con ontologías médicas, curación selectiva de fuentes y validación contextual automatizada mediante LLMs.

\begin{quote}
\small{Sobre la univalencia del diagnóstico de referencia, es crucial reconocer una limitación inherente al diseño de este y otros benchmarks similares: la asunción de un único diagnóstico de referencia (GDX) para cada caso. La práctica clínica real a menudo admite la \textbf{equifinalidad diagnóstica}, donde múltiples condiciones pueden explicar razonablemente un mismo cuadro clínico, especialmente en fases tempranas. El modelo de un único GDX no tiene en cuenta esta complejidad. Un modelo de IA podría proponer un diagnóstico alternativo perfectamente válido desde el punto de vista clínico que, al no coincidir con el GDX predefinido, sería incorrectamente penalizado por el pipeline \textbf{PV4}. Por ejemplo, ante un cuadro de dolor torácico agudo, tanto una ``pericarditis aguda'' como una ``disección aórtica'' podrían ser hipótesis plausibles dependiendo de los matices. Si el GDX es el primero y el modelo prioriza el segundo, \textbf{PV4} lo registraría como un fallo en la primera posición. Esta limitación, aunque común, es particularmente relevante en un estudio que busca medir la sutileza del juicio clínico y debe ser tenida en cuenta al interpretar la tasa de acierto bruta.}
\end{quote}

\newpage

\section{Evolución de los pipelines de evaluación}
El desarrollo de nuestro framework de evaluación ha sido un proceso iterativo, donde cada pipeline representó una hipótesis sobre la mejor manera de medir el rendimiento. Esta evolución fue necesaria para confrontar y resolver el fenómeno de la saturación de la tarea.

\begin{table}[H]
    \centering
    \caption{Evolución de los pipelines de evaluación: ventajas, inconvenientes y lecciones aprendidas.}
    \label{tab:pipeline_evolution}
    \renewcommand{\arraystretch}{1.5} 
    \begin{tabularx}{\linewidth}{@{} >{\bfseries}c X X X @{}} % Cambiado 'l' a 'c' para centrar las celdas de la primera columna
        \toprule
        \textbf{Pipeline} & \textbf{Ventajas} & \textbf{Inconvenientes} & \textbf{Lección} \\
        \midrule
        
        \makecell{\textbf{PV0} \\ \small(\textbf{BERT})} & 
        Simple, rápido y totalmente automatizado. Ideal para una primera criba de similitud semántica. &
        Ingenuo y ciego al contexto clínico. No distingue la sinonimia de la relevancia diagnóstica. & 
        La similitud textual por sí sola es una métrica insuficiente y profundamente engañosa para el diagnóstico. \\
        \midrule

        \makecell{\textbf{PV2} \\ \small(\textbf{ICD10}+\textbf{BERT})} &
        Introduce objetividad y estructura usando códigos médicos estándar. \textbf{BERT} actúa como red de seguridad. &
        Excesiva rigidez que causa la "paradoja del especialista castigado", penalizando respuestas más específicas. &
        La codificación estricta es demasiado frágil y no captura la flexibilidad inherente al lenguaje clínico. \\
        \midrule

        \makecell{\textbf{PV3} \\ \small(Juez \textbf{LLM})} &
        Comprende el contexto, los matices y las relaciones clínicas complejas que los códigos ignoran. &
        Excesivamente generoso, causando la "saturación de la tarea". Iguala los rendimientos y oculta diferencias. &
        Un juicio semántico sin restricciones no mide la precisión, solo una plausibilidad que enmascara el rendimiento real. \\
        \midrule
        
        \makecell{\textbf{PV4} \\ \small(Híbrido)} &
        Equilibra la objetividad de los códigos con la flexibilidad semántica, usando la posición para discriminar. &
        Mayor complejidad computacional y de implementación al requerir múltiples componentes y modelos. &
        La evaluación de alta fidelidad exige una cascada jerárquica que combine objetividad, semántica y prioridad. \\
        
        \bottomrule
    \end{tabularx}
\end{table}

\begin{itemize}[leftmargin=*]
    \item \textbf{PV0:} Fue el primer intento de automatización, utilizando exclusivamente un modelo \textbf{BERT} para medir la similitud semántica. Se aplicó principalmente a modelos de Hugging Face, entre ellos:
    \begin{itemize}
    \item \textbf{sakura-solar-instruct-carbon-yuk} [0.2813, 0.6521]
    \item \textbf{llama3-openbiollm-70b-zgh} [0.3979, 0.6439]
    \item \textbf{jonsnowlabs-medellama-3-8b-v2-0-bfs} [0.5052, 0.5971]
    \item \textbf{medgemma-27b-text-it} [0.4318, 0.5782]
    \end{itemize}

    \vspace{1mm}
    \footnotesize{\textit{Nota: El primer valor corresponde a una estimación de severidad realizada mediante juicio contextual con GPT; no es el objetivo central del estudio, pero contribuye a estructurar la representación de los resultados y facilita su interpretación. El segundo valor proviene de un modelo BERT que calcula similitud semántica entre enunciados.}}

    \normalsize{}
    \item \textbf{PV1/PV2 (\textbf{ICD10}+\textbf{BERT}):} Este pipeline introdujo un artefacto metodológico crítico que se produce cuando el evaluador, limitado a una coincidencia de códigos estricta, penaliza una hipótesis diagnóstica por una discrepancia en la \textbf{granularidad taxonómica}, a pesar de su validez clínica\footnote{Por ejemplo, si el modelo propone una entidad nosológica de alta especificidad como ``Glomerulonefritis membranoproliferativa tipo I'' y el diagnóstico de referencia está codificado a un nivel ontológico superior, como ``Síndrome nefrítico crónico'' (ICD-10: N03), el sistema acostumbrará a registrar un fallo.}. En esencia, la evaluación castiga una inferencia clínica superior por su incapacidad para resolver la subsunción semántica inherente a las jerarquías de codificación médica.


    \item \textbf{PV3 (Juez \textbf{LLM}):} Para corregir la rigidez anterior, este pipeline delegó la evaluación completa a un \textbf{Large Language Model} (\textbf{LLM}) que actuaba como "juez". Su capacidad de razonamiento contextual le permitió entender relaciones clínicas complejas, pero su excesiva "generosidad" llevó a la saturación de los resultados, como se discutirá en la siguiente sección.
\end{itemize}

La Figura \ref{fig:v0_v3_comparison} ilustra visualmente la diferencia en las distribuciones de resultados entre el enfoque de \textbf{PV0} (aplicado a modelos Hugging Face) y el de \textbf{PV3} (aplicado a modelos OpenAI), mostrando cómo diferentes metodologías producen "realidades" de rendimiento muy distintas.

\begin{figure}[H]
    \centering
    \includegraphics[width=1.0\linewidth]{imgs/04_both-together-v0-v4.jpg}
    \caption{Comparación visual entre los resultados de PV0 y PV3, que representan los extremos del espectro evaluativo: desde una métrica puramente textual (BERT) hasta juicios contextuales realizados por LLMs.}
    \label{fig:v0_v3_comparison}
\end{figure}

Estas diferencias metodológicas no son triviales; de hecho, son la clave para entender el fenómeno de la saturación.

\newpage

\section{Análisis del fenómeno de la saturación de la tarea}
Durante el desarrollo de nuestros pipelines, nos enfrentamos a un fenómeno tan persistente como problemático: la ``saturación de la tarea''. Con este término describimos la tendencia observada de que modelos de IA de diferentes generaciones y capacidades obtuvieran puntuaciones notablemente similares bajo ciertas métricas, creando una aparente meseta de rendimiento que contradecía el rápido avance teórico del campo. Este fenómeno no es una curiosidad, sino un obstáculo fundamental para la correcta valoración del progreso. Entenderlo es entender las trampas de la evaluación de la IA.

Este fenómeno se manifestó de formas distintas pero relacionadas en nuestros pipelines intermedios. Fue como observar un objeto distante a través de diferentes lentes: cada lente corregía una distorsión anterior, pero introducía una nueva, hasta que encontramos la combinación correcta que nos permitió ver con claridad.

\subsection{La distorsión de la rigidez (PV2)}
Nuestro primer intento de automatización (\textbf{PV2}) buscaba la objetividad a través de la rigidez de los códigos médicos (\textbf{ICD-10}) y la sinonimia (\textbf{BERT}). El resultado fue un sistema que, si bien era objetivo, era ingenuo. Penalizaba la precisión clínica superior (la ``paradoja del especialista castigado'') y era ciego a cualquier relación que no fuera una equivalencia terminológica. El ranking que producía era claro, pero estaba basado en una visión del mundo clínico excesivamente simplificada. La Figura \ref{fig:v2_vs_v3} muestra la distribución de puntuaciones de este sistema: un paisaje de picos discretos, reflejo de su naturaleza binaria, incapaz de capturar los matices.

\subsection{La distorsión de la generosidad: (PV3)}
Para corregir esta rigidez, \textbf{PV3} empleó un Juez \textbf{LLM}, esperando que su capacidad de razonamiento contextual proporcionara una evaluación más matizada. El resultado fue la manifestación más clara de la saturación. Como se observa en la Figura \ref{fig:v2_vs_v3}, las puntuaciones de todos los modelos se inflaron y se agruparon en una franja muy estrecha en el extremo superior de la escala. Un modelo de una generación anterior como \textbf{o1} obtuvo una puntuación casi idéntica a los de vanguardia como \textbf{o3}.

El motivo de este comportamiento es que el Juez \textbf{LLM}, al evaluar la ``plausibilidad clínica'', se había vuelto un evaluador excesivamente generoso. Entendía las relaciones causa-efecto, las manifestaciones clínicas y las asociaciones diagnósticas, y premiaba todas estas conexiones. Al hacerlo, eliminó la distinción crucial entre una respuesta \textbf{correcta y precisa} y una respuesta meramente \textbf{relevante y plausible}. Esta generosidad actuó como un gran ecualizador, borrando las diferencias de rendimiento y creando una falsa meseta. La tarea para los modelos ya no era ser preciso, sino sonar lo suficientemente convincente para otro \textbf{LLM}.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.7\linewidth]{imgs/pv12vspv3_v2.jpg}
    \caption{Comparativa directa de resultados entre el método \textbf{ICD10}+\textbf{BERT} (\textbf{PV2}) y el Juez \textbf{LLM} (\textbf{PV3}).}
    \label{fig:v2_vs_v3}
\end{figure}


\subsection{La naturaleza de la tarea y la naturaleza de los LLM}
La raíz de este fenómeno yace en la interacción de tres factores: la \textbf{definición de la tarea}, la \textbf{naturaleza probabilística de los \textbf{LLM}} y el \textbf{criterio de evaluación}. Nuestra tarea, generar una lista de 5 diagnósticos diferenciales, es fundamentalmente una tarea de recuperación y ranking de información, no de creación desde cero. Los \textbf{LLM} modernos, desde \textbf{o1} hasta \textbf{o3}, poseen bases de conocimiento vastas. Con un prompt claro y restrictivo, todos son capaces de identificar un conjunto de diagnósticos plausibles.

La diferencia entre un modelo bueno y uno excelente no reside tanto en \textit{si} puede encontrar el diagnóstico correcto, sino en con qué prioridad y confianza lo presenta. \textbf{PV3}, al ser tan generoso, fallaba en medir esta dimensión de priorización. \textbf{PV4} fue diseñado específicamente para resolver este problema, reintroduciendo la rigidez de forma controlada y haciendo de la \textbf{precisión posicional} un criterio de desempate clave. Al hacerlo, finalmente logramos romper la ilusión de la convergencia y medir lo que realmente importa: no solo el acierto, sino la calidad y priorización de ese acierto.

\section{Diseño y lógica de PV4}
\textbf{PV4} es el resultado de este proceso de aprendizaje. No es un método único, sino un sistema jerárquico que sintetiza las lecciones de sus predecesores, buscando un equilibrio entre la objetividad de los códigos y la inteligencia del análisis semántico.

\subsection{Análisis preliminar y justificación del diseño}
El diseño de \textbf{PV4} se fundamentó en un análisis detallado de los resultados intermedios producidos por el set de evaluación en pipelines anteriores. Este análisis mostró hechos clave que condicionaron su arquitectura:
\begin{enumerate}
    \item \textbf{\textbf{SNOMED CT} es la columna vertebral semántica.} Aunque la codificación es multiontológica, \textbf{SNOMED CT} es el sistema más prevalente, cubriendo el 76\% de los diagnósticos de referencia (\textbf{GDX}) y el 87\% de los diagnósticos diferenciales propuestos (\textbf{DDX}). Su rol es central para establecer coincidencias directas y fiables (\textbf{Nivel 1}).
    \item \textbf{La granularidad de \textbf{ICD-10} requiere flexibilidad.} Se construyó una matriz de transiciones para cuantificar la proximidad en la jerarquía \textbf{ICD-10}, mostrando que más del 92\% de las coincidencias clínicamente útiles se ubicaban a una arista de distancia (padre $\leftrightarrow$ hijo). En consecuencia, \textbf{PV4} considera como acierto válido cualquier hijo o padre inmediato en la jerarquía (Figura \ref{fig:icd10hierarchy}), superando la rigidez de un match exacto.
    \item \textbf{La inevitable brecha semántica del 43.3\%.} En 195 de los 450 casos (43.3\%), no existe ningún código compartido (\textbf{SNOMED}, \textbf{ICD-10} u \textbf{OMIM}) entre el diagnóstico de referencia y las cinco propuestas del modelo. Esta "brecha semántica" hace indispensable contar con métodos de validación que no dependan de ontologías, justificando el uso de \textbf{BERT} y \textbf{LLMs} (\textbf{Nivel 2}) para rescatar aciertos semánticamente cercanos pero no codificados.
\end{enumerate}

\begin{figure}[H]
    \centering
    \includegraphics[width=0.8\linewidth]{imgs/v40studyoficd10jerarquy.jpg}
    \caption{Matriz de transiciones jerárquicas entre el diagnóstico de referencia (GDX) y las propuestas del modelo (DDX), mostrando la frecuencia con que difieren en distintos niveles de la jerarquía CIE-10.}
    \label{fig:icd10hierarchy}
\end{figure}

Como se observa en la Figura~\ref{fig:icd10hierarchy}, la matriz de transiciones captura con qué frecuencia las predicciones del modelo (\textit{DDX}) divergen del diagnóstico de referencia (\textit{GDX}) a lo largo de los diferentes niveles jerárquicos\footnote{
Ejemplo ilustrativo de la jerarquía adaptada: 
\textbf{range}: Lesiones y consecuencias externas $\rightarrow$ 
\texttt{S};
\textbf{category}: Lesiones en muñeca y mano $\rightarrow$ 
\texttt{S60--S69};
\textbf{block}: Fracturas a nivel de muñeca y mano $\rightarrow$ 
\texttt{S62};
\textbf{sub-block}: Fractura de metacarpiano (otro/no especificado) $\rightarrow$ 
\texttt{S62.3};
\textbf{group}: Fractura no especificada de metacarpiano $\rightarrow$ 
\texttt{S62.30};
\textbf{subgroup}: Fractura no especificada del segundo metacarpiano, encuentro inicial $\rightarrow$ 
\texttt{S62.301A}.
}
 de la CIE-10: desde niveles generales como \textit{Range} (rango) hasta niveles muy específicos como \textit{Subgroup} (subgrupo).

Los colores indican la densidad de ocurrencias: celdas en rojo representan transiciones con alta frecuencia, mientras que los tonos más claros indican menor frecuencia. Es evidente que la mayoría de las discrepancias se dan entre niveles adyacentes, como \textit{Categoría} $\rightarrow$ \textit{Bloque} o \textit{Bloque} $\rightarrow$ \textit{Sub-bloque}, lo cual sugiere que, aunque no se alcance coincidencia exacta, las propuestas del modelo suelen ser jerárquicamente próximas y clínicamente relevantes.

Este hallazgo justifica el diseño de la métrica \textbf{PV4}, que no se limita a validar coincidencias exactas, sino que también reconoce como válidas aquellas predicciones que coinciden con el diagnóstico real en un nivel jerárquicamente relacionado: padre, hijo o hermano. Así, se evita penalizar al modelo por aciertos clínicamente válidos que no coinciden exactamente en código, pero sí en significado médico.

\subsection{Lógica operativa y flujo de decisión}
La lógica de \textbf{PV4} es una cascada determinista que evalúa cada una de las 5 propuestas diagnósticas (\textbf{DDX}) de un modelo en orden, desde la posición 1 hasta la 5. El proceso se detiene en cuanto encuentra la primera coincidencia válida con el diagnóstico de referencia (\textbf{GDX}), y la puntuación del caso se determina por la posición de ese primer acierto. Esto prioriza la confianza clínica del modelo.

Para cada \textbf{DDX} individual, el pipeline (Figura \ref{fig:pv4_flowchart}) sigue una jerarquía de validación que va de lo más objetivo a lo más interpretativo:

\begin{enumerate}[leftmargin=*, label=\textbf{Nivel \arabic*:}]
    \item \textbf{Verificación por códigos (máxima objetividad):} Se busca una coincidencia de código \textbf{SNOMED CT} (match exacto). Si no se encuentra, se verifica una coincidencia \textbf{ICD-10} (exacta, padre, hijo o hermano). Si cualquiera de estos métodos tiene éxito, el \textbf{DDX} se considera un acierto, el caso se da por resuelto y se registra su posición.
    \item \textbf{Juicio semántico (red de seguridad):} Solo si los códigos fallan, se recurre al análisis semántico. Primero, se evalúa si la similitud del coseno de \textbf{BERT} supera un umbral de alta confianza ($>0.925$). Si es así, se considera un acierto.
    \item \textbf{Desempate semántico:} Si la similitud \textbf{BERT} no alcanza el umbral de alta confianza ($<0.89$), se activa un juicio competitivo. Se consulta un \textbf{Juez LLM} que evalúa la relación semántica entre el \textbf{DDX} y el \textbf{GDX}. Si ambos métodos coinciden en que hay un acierto, se elige el diagnóstico que aparece en una posición más alta dentro de la lista original de diferenciales, premiando la capacidad de priorización del modelo. Si solo uno lo valida, se acepta su veredicto. Si ninguno identifica una relación válida, el \textbf{DDX} se descarta.
\end{enumerate}
Este proceso se repite para cada \textbf{DDX} en la lista hasta que se encuentra un acierto o se agotan las 5 propuestas.

\begin{figure}[H]
    \centering
    \begin{tikzpicture}[node distance=1.5cm and 1cm, scale=0.85, transform shape]
% --- NODOS ---
% Columna principal del pipeline
\node (in)   [proc] {\textbf{DDX} candidato};
\node (sno)  [proc, below=of in, fill=snomed!25] {\textbf{SNOMED}};
\node (icd)  [proc, below=of sno, fill=icd!20] {\textbf{ICD10} HIERARCHY};
\node (bert) [proc, below=of icd, fill=bert!20] {\textbf{BERT} $\cos\theta>0.925$};
\node (dec)  [dec,  below=of bert, node distance=2.1cm] {$0.89<\cos\theta?$};

% LLM node (a la derecha del decisor)
\node (llm)  [proc, right=2.5cm of dec, fill=llm!20] {\textbf{LLM}\\JUDGMENT};

% Nodo de salida (debajo, a la izquierda)
\node (out)  [out, below=of dec, node distance=2.5cm, xshift=-3.5cm] {Match};

% --- ARISTAS ---
% Flujo principal (casos sin resolver)
\draw[line] (in)   -- (sno);
\draw[line] (sno)  -- (icd)  node[midway, right, xshift=7mm] {\footnotesize No};
\draw[line] (icd)  -- (bert) node[midway, right, xshift=7mm] {\footnotesize No};
\draw[line] (bert) -- (dec)  node[midway, right, xshift=7mm] {\footnotesize No};

% Salidas de los casos resueltos
\draw[line] (sno.west)  -| (out.north) node[very near start, above, xshift=-30mm] {\footnotesize Sí};
\draw[line] (icd.west) -| (out.north) node[very near start, above, xshift=-27mm] {\footnotesize Sí};
\draw[line] (bert.west) -| (out.north) node[very near start, above, xshift=-28mm] {\footnotesize Sí};

% Decisión: Sí va directo a Match
\draw[line] (dec.south) |- (out.east) node[very near start, right] {Sí};

% Decisión: No va al LLM
\draw[line] (dec.east) -- (llm.west) node[midway, above] {No};

% LLM a salida final
\draw[line] (llm.south) |- (out.east);

    \end{tikzpicture}
    \caption{Diagrama de flujo del proceso de evaluación de \textbf{PV4} para un único \textbf{DDX}, mostrando su cascada jerárquica.}
    \label{fig:pv4_flowchart}
\end{figure}

\section{Resultados y análisis de PV4}
La aplicación de este marco de alta fidelidad mostró una jerarquía de rendimiento clara y robusta, cuya sensibilidad nos permitió no solo comparar modelos, sino también el impacto de la ingeniería de prompts.

\subsection{Análisis preliminar de la distribución de métodos (PV4)}
Antes de analizar el rendimiento de los modelos, es crucial entender el comportamiento del propio pipeline de evaluación. Un análisis preliminar sobre un subconjunto de casos (Figura \ref{fig:methods_distribution}) muestra cómo se distribuyen las resoluciones entre los distintos métodos de \textbf{PV4}. Se observa que la combinación de \textbf{SNOMED} (coincidencia exacta) y el \textbf{Juez LLM} (juicio semántico) explican la gran mayoría de los aciertos, con un \textbf{76.16\%} del total. Esto confirma que la objetividad de los códigos es la base, pero se necesita un evaluador contextual para los casos semánticamente complejos. Por su parte, \textbf{ICD-10} (12.16\%) y \textbf{BERT} (11.68\%) actúan como mecanismos secundarios pero importantes para capturar relaciones jerárquicas y sinonimias no cubiertas por el primer nivel.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.9\linewidth]{imgs/v4horizontalstackedbarsbymodelacrossmethods_v2.jpg}
    \caption{Estudio preliminar del desglose de los métodos de resolución del pipeline \textbf{PV4}. Muestra la contribución de cada componente (\textbf{SNOMED match}, \textbf{ICD10 exact-sibling-parent}, \textbf{BERT autoconfirm}, \textbf{BERT match} y \textbf{LLM}) a la validación de aciertos.}
    \label{fig:methods_distribution}
\end{figure}

\subsection{Optimización de prompts y su impacto en el rendimiento}
El benchmark no solo permite comparar modelos, sino también la eficacia de diferentes prompts. La sensibilidad de \textbf{PV4} nos ha permitido cuantificar cómo la estructura del prompt influye en la calidad de la respuesta, mostrando patrones clave para la optimización. La Figura \ref{fig:prompt_battle_prompt} ilustra la variabilidad del rendimiento en función del prompt utilizado para un mismo modelo y viceversa. En el \textbf{Anexo B} se adjuntan los prompts que obtuvieron los mejores resultados.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.8\linewidth]{imgs/prompt_battle_by_prompt.jpg}
    \caption{Comparativa de rendimiento entre diferentes variantes de prompts. Las cruces indican ejecuciones con \textbf{o3} y los círculos con \textbf{4o}; los colores, distintos prompts (para una versión de esta gráfica con cada prompt identificado por su nombre, facilitando un análisis más granular, véase el \textbf{Anexo C}.).}
    \label{fig:prompt_battle_prompt}
\end{figure}

Un análisis más detallado sobre el tipo de salida solicitado en el prompt arroja conclusiones significativas (Tabla \ref{tab:prompt_format_impact}). Exigir un razonamiento explícito, como listar síntomas a favor y en contra, produce el mejor equilibrio entre posición promedio y tasa de acierto. En contraste, sobrecargar el modelo pidiendo campos como \texttt{confidence} o \texttt{rationale} degrada el rendimiento de la tarea principal.

\begin{table}[H]
\centering
\caption{Impacto del formato de salida del prompt en el rendimiento.}
\label{tab:prompt_format_impact}
\begin{tabularx}{\linewidth}{Xlcc}
\toprule
\textbf{Tipo de Salida Solicitada} & \textbf{Nº Prompts} & \textbf{PPos Media} & \textbf{\% Acierto Medio} \\
\midrule
Lista sencilla de strings & 9 & 1.630 & 88.36\% \\
Objeto con \textit{rationale} + \textit{confidence} & 6 & 1.604 & 77.42\% \\
\textbf{Objeto con síntomas (in/out)} & \textbf{6} & \textbf{1.506} & \textbf{91.44\%} \\
Objeto con síntomas + envoltura XML & 3 & 1.560 & 93.48\% \\
\bottomrule
\end{tabularx}
\end{table} 

Además, se observó que la longitud y la complejidad del prompt interactúan de forma decisiva. Los prompts más largos ($>160$ palabras) tienden a mejorar la tasa de acierto, pero este beneficio se anula si el formato de salida es demasiado complejo. Finalmente, incluir cláusulas "failsafe'' en el prompt principal penaliza ligeramente el rendimiento, sugiriendo que la validación del tipo de input debe ser un paso previo.


\subsection{Análisis comparativo y ranking final de modelos}
El análisis culmina con la comparación directa de los modelos, utilizando los datos agregados de múltiples ejecuciones para mitigar la variabilidad. La Tabla \ref{tab:final_ranking} presenta los resultados consolidados.

\begin{table}[H]
\centering
\caption{Ranking y métricas clave de rendimiento por modelo (\textbf{PV4}).}
\label{tab:final_ranking}
\begin{tabularx}{\linewidth}{lXXXX}
\toprule
\textbf{Métrica} & \textbf{o3} & \textbf{o1} & \textbf{o3-pro} & \textbf{4o} \\
\midrule
\textbf{Tasa de Acierto (\%)} & 93.65\% & 91.44\% & \textbf{96.40\%} & 94.31\% \\
\textbf{Posición Promedio} & \textbf{1.474} & 1.585 & 1.597 & 1.629 \\
Aciertos en Posición 1 (P1) & \textbf{311} & 305 & 299 & 299 \\
Aciertos en Posición 5 (P5) & \textbf{9} & 17 & 24 & 20 \\
\bottomrule
\end{tabularx}
\end{table}

A primera vista, los resultados exhiben una dicotomía: \textbf{o3-pro} obtiene la máxima tasa de acierto, mientras que \textbf{o3} logra la mejor posición promedio. Un análisis estadístico y cualitativo es indispensable para resolver esta tensión y determinar el verdadero rendimiento.

\subsubsection{Confianza y estabilidad estadísticas}

La métrica más relevante para la utilidad clínica es la \textbf{posición promedio}, pues indica la capacidad de priorización del modelo. Aquí, \textbf{o3} lidera de forma contundente (1.474). Un test de significancia estadística (Prueba U de Mann-Whitney) contra su rival más cercano, \textbf{o3-pro} (1.597), arroja un \textbf{valor p $<$ 0.001}. Esto confirma que la superioridad de \textbf{o3} en la priorización del diagnóstico es \textbf{estadísticamente muy significativa} y no fruto del azar.

Esta calidad de priorización se refleja en el número de aciertos en primera posición (P1), donde \textbf{o3} también lidera con 311 casos, como se visualiza en la Figura \ref{fig:top_positions}.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.6\linewidth]{imgs/v4horizontalstackedtoppositions.jpg}
    \caption{Distribución de los aciertos en las Top 5 posiciones por modelo.}
    \label{fig:top_positions}
\end{figure}

Además, \textbf{o3} demuestra una \textbf{estabilidad} superior. Al comparar la variabilidad de su rendimiento frente al modelo más reciente, \textbf{4o}, se observa que el coeficiente de variación (CV) de la tasa de acierto de \textbf{o3} (0.026) es cuatro veces menor que el de \textbf{4o} (0.106). Esto convierte a \textbf{o3} en un modelo mucho más predecible y robusto para entornos de producción.

\subsubsection{Cobertura en la tasa de aciertos}

Aunque \textbf{o3-pro} presenta una tasa de acierto nominalmente superior (96.40\% vs. 93.65\%), un análisis estadístico (Test Z para dos proporciones) revela que esta diferencia no es significativa, con un \textbf{valor p de 0.11}. Al ser p $>$ 0.05, no podemos concluir que \textbf{o3-pro} sea realmente superior en cobertura; la diferencia observada es probablemente casual.

El desglose de los métodos de resolución (Figura \ref{fig:casecount_method}) explica cómo \textbf{o3-pro} alcanza esta aparente ventaja. El modelo se apoya más en el "juicio semántico del LLM", un método más flexible, mientras que \textbf{o3} basa una mayor proporción de sus aciertos en la disciplina taxonómica de los códigos \textbf{SNOMED} e \textbf{ICD10}. En esencia, \textbf{o3-pro} "compra" una cobertura marginalmente mayor (y estadísticamente no significativa) a costa de sacrificar la precisión en el ranking y la rigurosidad metodológica.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.9\linewidth]{imgs/v4casecountandaveragepositionbymethod.jpg}
    \caption{Número de casos resueltos y posición promedio por cada método y modelo. Los tonos más oscuros representan mejor puntuación.}
    \label{fig:casecount_method}
\end{figure}

\section{Discusión}
La metodología incremental documentada en este informe nos ha llevado a una conclusión compleja y matizada. Si bien \textbf{PV4} representa nuestro esfuerzo más sofisticado por medir el rendimiento de la IA diagnóstica, sus resultados, lejos de ofrecer una respuesta definitiva, nos enfrentan a una manifestación aún más sutil del fenómeno de la saturación de la tarea.

\subsection{Análisis crítico de los resultados de PV4}
A primera vista, \textbf{PV4} establece una jerarquía clara. Sin embargo, una mirada más crítica muestra un panorama complejo. El modelo \textbf{o3-pro} alcanza la máxima tasa de acierto, pero a costa de una peor priorización y mayor dependencia de la evaluación semántica. Por otro lado, \textbf{o3} emerge como el modelo con el \textbf{rendimiento más estable y predecible}, con la mejor posición promedio y la menor variabilidad entre prompts. Esta tensión entre \textbf{cobertura (\textbf{o3-pro}) y calidad de priorización (\textbf{o3})} es un hallazgo clave.

La diferencia en la tasa de acierto entre los modelos de alto rendimiento es relativamente estrecha, lo que podría interpretarse como una señal de saturación. Planteamos la siguiente hipótesis: el dataset de 450 casos, a pesar de su diversidad, podría estar concentrado en un espectro de dificultad que se resuelve mediante un "reconocimiento de patrones" altamente sofisticado, más que un "razonamiento de primeros principios". Si la mayoría de los casos se resuelven identificando constelaciones de síntomas que los modelos ya han internalizado masivamente, es lógico que converjan en rendimiento. La tarea no estaría midiendo su capacidad de ``pensar'', sino la exhaustividad de su ``memoria'' de patrones clínicos.

\subsection{Significancia estadística e incertidumbre}
La consistencia de los resultados a través de 450 casos diversos y múltiples variantes de prompts aporta una base empírica razonable para las conclusiones. La ventaja posicional y de estabilidad de \textbf{o3} sobre \textbf{4o} es estadísticamente notable, como demuestra la diferencia de cuatro veces en su coeficiente de variación. De manera similar, la dicotomía entre la tasa de acierto de \textbf{o3-pro} y la calidad del ranking de \textbf{o3} es un patrón robusto. Por tanto, consideramos que la jerarquía y los perfiles de rendimiento observados son señales significativas dentro del marco evaluado, más que artefactos del azar.

En este contexto, \textbf{PV4} ha demostrado tener un poder discriminativo suficiente no solo para rankear modelos, sino para caracterizar sus perfiles de rendimiento (p. ej., estabilidad, confianza vs. cobertura) y para guiar la ingeniería de prompts.

\subsection{El riesgo del sesgo autorreferencial en el juicio semántico}
\label{sec:llm_bias}

El sistema de evaluación en tres etapas de PV4 reduce en gran medida las discrepancias determinísticas y semánticas que afectaban a evaluaciones anteriores. No obstante, el Nivel 3 sigue resolviendo una pequeña fracción de empates recurriendo a un juez LLM independiente. Dado que este juez es, en sí mismo, un modelo de lenguaje, existe —al menos en principio— la posibilidad de que favorezca respuestas cuya redacción, estilo de razonamiento o representaciones latentes se asemejen a las suyas propias, en lugar de valorar exclusivamente la corrección clínica.

Para asegurarnos de que este riesgo de "homofilia" se mantuviera en el plano teórico y no práctico, instrumentamos el sistema para registrar cada vez que se invocaba al juez LLM, junto con las respuestas candidatas y la justificación ofrecida por el juez. Posteriormente, analizamos una muestra de estos casos de forma manual y los contrastamos con etiquetas de referencia.

Dado que estas medidas de control formaron parte del flujo de análisis desde el principio, tenemos la confianza de que cualquier posible sesgo autorreferencial residual es insignificante en comparación con el desempeño diagnóstico observable. En resumen, el juez LLM actúa como un mecanismo de respaldo útil, sin distorsionar la clasificación general de los modelos.

\section{Conclusiones}

El proceso iterativo de diseño y validación de pipelines nos ha proporcionado una comprensión profunda no solo del rendimiento de los modelos, sino de la naturaleza misma de la evaluación de IA en un dominio tan complejo como el diagnóstico clínico. Las conclusiones se pueden estructurar en tres áreas clave: el rendimiento de los modelos, las lecciones sobre la metodología y las directrices para la ingeniería de prompts.

\medskip
\noindent\textbf{Veredicto del rendimiento de los modelos}
\begin{itemize}[nosep] % Al quitar 'leftmargin=*', se usa la sangría por defecto
    \item \textbf{o3} destaca por su fiabilidad: mejor posición promedio (1,47) y mayor número de aciertos en P1.
    \item \textbf{o3-pro} logra la máxima cobertura (96,4\% de aciertos) a costa de una peor priorización en el ranking.
    \item La estabilidad de \textbf{o3} contrasta con la alta variabilidad de \textbf{4o}, haciéndolo más predecible para producción.
    \item La estrecha diferencia de rendimiento global sugiere que la tarea se acerca a un límite de discriminación.
\end{itemize}

\medskip
\noindent\textbf{Lecciones sobre la metodología de evaluación}
\begin{itemize}[nosep]
    \item \textbf{PV2} (\textbf{ICD10}+\textbf{BERT}) demostró que la rigidez de códigos castiga injustamente la especificidad clínica superior.
    \item \textbf{PV3} (Juez \textbf{LLM}) enseñó que la generosidad semántica crea una falsa convergencia de rendimientos (saturación).
    \item \textbf{PV4} funciona al combinar objetividad (códigos) y semántica (\textbf{LLM}), usando la posición como desempate clave.
    \item El evaluador no es un observador pasivo; define activamente la métrica de éxito de la tarea.
\end{itemize}

\medskip
\noindent\textbf{Claves para la ingeniería de prompts}
\begin{itemize}[nosep]
    \item Exigir un razonamiento estructurado (síntomas a favor/en contra) mejora la precisión del diagnóstico principal.
    \item Sobrecargar el prompt con tareas secundarias (\texttt{confidence}, \texttt{rationale}) degrada el rendimiento de la tarea primaria.
    \item Las cláusulas de seguridad (\texttt{FAILSAFE}) penalizan el rendimiento; la validación debe ser un paso previo.
\end{itemize}

\newpage
\begin{appendices}

\section{Composición detallada del dataset de evaluación}
El dataset final de 450 casos utilizado para la evaluación comparativa de los modelos se construyó a partir de un universo de 9.677 casos clínicos agregados de siete fuentes diferentes. La selección no fue aleatoria, sino que se basó en un proceso de Extracción, Transformación y Carga (ETL) diseñado para garantizar la diversidad y representatividad del conjunto de pruebas. El siguiente diagrama de Sankey (Figura \ref{fig:sankey_appendix}) visualiza este flujo, mostrando cómo los casos de cada fuente original contribuyen al dataset final. Este método de muestreo estratificado es fundamental para asegurar que los resultados de la evaluación sean robustos y generalizables.

\begin{figure}[H]
    \centering
    \includegraphics[width=1.0\linewidth]{imgs/08_etl_visualized_as_sankey_at_20250708.png}
    \caption{Diagrama de Sankey que visualiza el proceso de ETL para la composición del dataset de evaluación de 450 casos a partir de las fuentes originales.}
    \label{fig:sankey_appendix}
\end{figure}

\newpage


\section{Análisis detallado del rendimiento por prompt}
\label{app:prompt_comparison}

La siguiente figura ofrece una versión detallada y etiquetada de la Figura \ref{fig:prompt_battle_prompt} del cuerpo principal del informe. Esta visualización permite correlacionar directamente el rendimiento (posición promedio y tasa de acierto) de cada punto de datos con un prompt específico, cuyos textos completos se pueden consultar en el Anexo C.

Para garantizar la total transparencia y reproducibilidad de este estudio, el código fuente completo de todos los prompts, así como los scripts de evaluación y los datasets anonimizados, están disponibles en el repositorio público del proyecto en GitHub.

\begin{figure}[H]
    \centering
    \includegraphics[width=1.0\linewidth]{imgs/prompt_battle_by_prompt_labeled.jpg}
\caption{
Comparativa etiquetada del rendimiento entre distintos prompts. Cada etiqueta identifica un prompt específico empleado durante las ejecuciones (los nombres pueden incluir referencias a modelos, pero únicamente reflejan la base sobre la que se realizaron ajustes evolutivos en el diseño del prompt, sin implicar un cambio de modelo subyacente).
}

\label{fig:prompt_battle_labeled}
\end{figure}

\newpage

\section{Prompts con mayor rendimiento}
\label{app:prompts}
A continuación se presentan los prompts que obtuvieron los mejores resultados para los modelos \textbf{o3} y \textbf{4o}, junto con sus puntuaciones de rendimiento (posición promedio y tasa de acierto).

\subsection{Mejores prompts para \textbf{o3} (TOP4)}

\subsubsection*{classic\_v2}
\textbf{Puntuación: 1.326 - 92.7\%}
\begin{verbatim}
You are a diagnostic assistant. Given the patient case below, generate N possible
diagnoses. For each:

- Give a brief description of the disease  
- List symptoms the patient has that match the disease  
- List patient symptoms that are not typical for the disease  

Output format:  
Return a JSON array of N objects, each with the following keys:  
- "diagnosis": disease name  
- "description": brief summary of the disease  
- "symptoms_in_common": list of matching symptoms  
- "symptoms_not_in_common": list of patient symptoms not typical of that disease  

Output only valid JSON (no extra text, no XML, no formatting wrappers).  

Example:  
```json
[
  {{
    "diagnosis": "Disease A",
    "description": "Short explanation.",
    "symptoms_in_common": ["sx1", "sx2"],
    "symptoms_not_in_common": ["sx3", "sx4"]
  }},
  ...
]

PATIENT DESCRIPTION:
{case_description}
\end{verbatim}

\subsubsection*{classic\_v4}
\textbf{Puntuación: 1.422 - 90.7\%}
\begin{verbatim}
You are a diagnostic assistant. Given the patient case below, generate N possible
diagnoses. For each:

- Give a brief description of the disease  
- List symptoms the patient has that match the disease  
- List patient symptoms that are not typical for the disease  

Output format:  
Return a JSON array of N objects, each with the following keys:  
- "diagnosis": disease name  
- "description": brief summary of the disease  
- "symptoms_in_common": list of matching symptoms  
- "symptoms_not_in_common": list of patient symptoms not typical of that disease  

Output only valid JSON (no extra text, no XML, no formatting wrappers).  

Example:  
```json
[
  {{
    "diagnosis": "Disease A",
    "description": "Short explanation.",
    "symptoms_in_common": ["sx1", "sx2"],
    "symptoms_not_in_common": ["sx3", "sx4"]
  }},
  ...
]

PATIENT DESCRIPTION:
{case_description}
\end{verbatim}

\subsubsection*{classic\_v1 (original)}
\textbf{Puntuación: 1.468 - 94.35\%}
\begin{verbatim}
Behave like a hypothetical doctor tasked with providing N hypothesis diagnosis for a
patient based on their description. Your goal is to generate a list of N potential 
diseases, each with a short description, and indicate which symptoms the patient has
in common with he proposed disease and which symptoms the patient does not have
in common.
 
Carefully analyze the patient description and consider various potential diseases 
that could match the symptoms described. For each potential disease:
1. Provide a brief description of the disease
2. List the symptoms that the patient has in common with the disease
3. List the symptoms that the patient has that are not in common with the disease
       
Present your findings in a JSON format within XML tags. The JSON should contain 
the following keys for each of the N potential disease:
- "diagnosis": The name of the potential disease
- "description": A brief description of the disease
- "symptoms_in_common": An array of symptoms the patient has that match the disease
- "symptoms_not_in_common": An array of symptoms the patient has that are not 
                            in common with the disease
       
Here's an example of how your output should be structured:
       
<diagnosis_output>
[
{{
    "diagnosis": "some disease 1",
    "description": "some description",
    "symptoms_in_common": ["symptom1", "symptom2", "symptomN"],
    "symptoms_not_in_common": ["symptom1", "symptom2", "symptomN"]
}},
...
{{
    "diagnosis": "some disease n",
    "description": "some description",
    "symptoms_in_common": ["symptom1", "symptom2", "symptomN"],
    "symptoms_not_in_common": ["symptom1", "symptom2", "symptomN"]
}}
]
</diagnosis_output>
       
Present your final output within <diagnosis_output> tags as shown in the example above.
       
Here is the patient description:
<patient_description>
{case_description}
</patient_description>
\end{verbatim}

\subsubsection*{claude\_sonnet\_4}
\textbf{Puntuación: 1.471 - 91.8\%}
\begin{verbatim}
Generate 5 differential diagnoses from the clinical case below.

ANALYSIS: Consider common through rare conditions, metabolic/structural causes,
demographics, timeline, and clinical epidemiology. Prioritize treatable conditions.

OUTPUT: JSON array of objects:
[{{"dx":"Disease","rationale":"Brief reason","confidence":"High/Medium/Low"}}]

CASE: {case_description}
\end{verbatim}

\subsection{Mejores prompts para \textbf{4o} (TOP4)}

\subsubsection*{\textit{classic\_v2}}
\textit{Este prompt, ya presentado en la sección anterior, también obtiene el mejor rendimiento para el modelo \textbf{4o}.}

\subsubsection*{classic\_v1 (sin \texttt{description})}
\begin{verbatim}
Behave like a hypothetical doctor tasked with providing N hypothesis diagnosis for a
patient based on their description. Your goal is to generate a list of N potential  
diseases and indicate which symptoms the patient has in common with the proposed
disease and which  symptoms the patient does not have in common.
 
Carefully analyze the patient description and consider various potential diseases 
that could match the symptoms described. For each potential disease:
1. List the symptoms that the patient has in common with the disease
2. List the symptoms that the patient has that are not in common with the disease
       
Present your findings in a JSON format within XML tags. The JSON should contain 
the following keys for each of the N potential disease:
- "diagnosis": The name of the potential disease
- "symptoms_in_common": An array of symptoms the patient has that match the disease
- "symptoms_not_in_common": An array of symptoms the patient has that are not 
                            in common with the disease
       
Here's an example of how your output should be structured:
       
<diagnosis_output>
[
{{
    "diagnosis": "some disease 1",
    "symptoms_in_common": ["symptom1", "symptom2", "symptomN"],
    "symptoms_not_in_common": ["symptom1", "symptom2", "symptomN"]
}},
...
{{
    "diagnosis": "some disease n",
    "symptoms_in_common": ["symptom1", "symptom2", "symptomN"],
    "symptoms_not_in_common": ["symptom1", "symptom2", "symptomN"]
}}
]
</diagnosis_output>
       
Present your final output within <diagnosis_output> tags as shown in the example above.
       
Here is the patient description:
<patient_description>
{case_description}
</patient_description>
\end{verbatim}

\subsubsection*{4o\_4}
\begin{verbatim}
TASK: Given the patient case, return 5 most likely diagnoses (ranked).

RULES:
• Include only diseases that plausibly explain most symptoms.
• Use standard medical terms (precise, specific).
• Always include rare/treatable/metabolic if fitting.
• Prefer unifying Dx > partials.
• Penalize weak matches or noise.
• If input is not a clinical scenario (no patient-specific findings), return: []

OUTPUT → Valid JSON array (no text, no comments):
["Diagnosis 1","Diagnosis 2","Diagnosis 3","Diagnosis 4","Diagnosis 5"]

PATIENT:
{case_description}
\end{verbatim}

\subsubsection*{claude\_opus\_1}
\begin{verbatim}
You are a world-class diagnostic clinician with expertise across all medical specialties. 
Generate exactly 5 differential diagnoses for the patient case below.

CRITICAL INSTRUCTIONS:
- Rank diagnoses by probability given ALL clinical features (most to least likely)
- Consider the COMPLETE clinical picture: demographics, timeline, severity, progression
patterns
- Include ALL plausible conditions: common, rare, genetic, metabolic, structural,
infectious, autoimmune
- Weight classic presentations heavily but don't ignore atypical variants
- Never dismiss treatable conditions regardless of rarity
- Apply Occam's razor AND Hickam's dictum appropriately

OUTPUT FORMAT: Return ONLY a JSON array of disease names as strings, nothing else.
Example: ["Disease A","Disease B","Disease C","Disease D","Disease E"]

CLINICAL CASE:
{case_description}
\end{verbatim}

\end{appendices}

\end{document}