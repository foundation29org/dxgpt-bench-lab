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
\begin{titlepage}
    \centering
    \vspace*{2cm}
    
    {\Huge\bfseries\color{primarycolor} Informe sobre la evaluación de modelos de IA para soporte al diagnóstico clínico}
    
    \vspace{1.5cm}
    
    {\Large\bfseries Análisis metodológico de PV0-PV4}
    
    \vspace{2.5cm}
    
    \begin{flushleft}
    \large
    \begin{tabular}{@{}l}
        \textbf{Autores:} Yago Mendoza, Javier Logroño\\
        \textbf{Institución:} Foundation 29 \\
        \textbf{Fecha:} \today \\
        \textbf{Versión del Documento:} 2.1 \\
    \end{tabular}
    \end{flushleft}
    
    \vfill
    
    \textit{\small Este documento presenta un análisis pormenorizado de los hallazgos y la evolución de los marcos de evaluación para la herramienta de diagnóstico asistido por IA DxGPT, abarcando desde estudios clínicos iniciales hasta el desarrollo de pipelines automatizados de alta fidelidad.}
    
\end{titlepage}
\newpage

\begin{center}
    {\Large \textbf{Resumen}}\\[1em]  % \LARGE hace el texto más grande, [1em] agrega espacio debajo
\end{center}

Este informe describe la evolución metodológica y los resultados de la evaluación de cuatro modelos de lenguaje de OpenAI —\textbf{GPT-4o, o1, o3 y o3-pro}— sobre \textbf{450 casos pediátricos}. El análisis demostró que los evaluadores iniciales producían \textbf{realidades distorsionadas}: un pipeline basado en códigos (\textbf{PV2}: \textbf{ICD-10} + \textbf{BERT}) \textbf{penalizaba la especificidad clínica} (la ``\textbf{paradoja del especialista castigado}''), mientras que un juez-\textbf{LLM} (\textbf{PV3}) provocaba una \textbf{convergencia artificial de rendimientos} al premiar la \textbf{plausibilidad sobre la precisión}. Para superar esta limitación, se desarrolló \textbf{PV4}, un \textbf{pipeline jerárquico} que combina la \textbf{objetividad de los códigos} (\textbf{SNOMED, ICD-10}) con el \textbf{juicio semántico} (\textbf{BERT, LLM}), e introduce una métrica clave: \textbf{la posición en la lista diferencial} como indicador de \textbf{confianza clínica}. Esta innovación metodológica \textbf{rompió la saturación de la tarea} y reveló una \textbf{jerarquía de rendimiento clara}. El modelo \textbf{o3} emergió como el más confiable y estable, con la \textbf{mejor posición promedio} (1{,}47) y el \textbf{mayor número de aciertos en primera posición} (311), a pesar de que \textbf{o3-pro} obtuvo una \textbf{tasa de acierto bruta marginalmente superior} (96{,}4\%). Este último, sin embargo, lo logró a costa de una \textbf{peor priorización} (posición media de 1{,}60) y una \textbf{mayor dependencia del evaluador semántico}. El análisis de \textbf{prompts} confirmó que \textbf{exigir razonamiento explícito} —por ejemplo, \textbf{listar síntomas a favor y en contra}— es la \textbf{estrategia más eficaz}, superando tanto a los formatos más simples como a aquellos que sobrecargan al modelo solicitando campos adicionales como la \textit{confianza}.




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
El dataset de 450 casos fue seleccionado para asegurar una amplia cobertura de patologías, garantizando que la evaluación no estuviera sesgada hacia una especialidad concreta, como se muestra en la Figura \ref{fig:diversity}.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.9\linewidth]{imgs/00_all_450_diversity_visualized.jpeg}
    \caption{Distribución de los 450 casos clínicos por capítulos de la codificación \textbf{ICD-10}.}
    \label{fig:diversity}
\end{figure}

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
        \item \textbf{sakura-solar-instruct-carbon-yuk}
        \item \textbf{llama3-openbiollm-70b-zgh}
        \item \textbf{jonsnowlabs-medellama-3-8b-v2-0-bfs}
        \item \textbf{medgemma-27b-text-it}
    \end{itemize}
    Su limitación era la incapacidad para entender el contexto clínico o las relaciones jerárquicas, reduciendo la evaluación a una simple comparación de proximidad textual.

    \item \textbf{PV1/PV2 (\textbf{ICD10}+\textbf{BERT}):} Representó un salto en sofisticación al introducir los códigos \textbf{ICD-10} como primer criterio de evaluación. Si la coincidencia de código fallaba, se utilizaba \textbf{BERT} como red de seguridad. Este método, aunque más estructurado, introdujo la ``paradoja del especialista castigado'', penalizando respuestas clínicamente superiores pero terminológicamente más específicas.

    \item \textbf{PV3 (Juez \textbf{LLM}):} Para corregir la rigidez anterior, este pipeline delegó la evaluación completa a un \textbf{Large Language Model} (\textbf{LLM}) que actuaba como "juez". Su capacidad de razonamiento contextual le permitió entender relaciones clínicas complejas, pero su excesiva "generosidad" llevó a la saturación de los resultados, como se discutirá en la siguiente sección.
\end{itemize}

La Figura \ref{fig:v0_v3_comparison} ilustra visualmente la diferencia en las distribuciones de resultados entre el enfoque de \textbf{PV0} (aplicado a modelos Hugging Face) y el de \textbf{PV3} (aplicado a modelos OpenAI), mostrando cómo diferentes metodologías producen "realidades" de rendimiento muy distintas.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.9\linewidth]{imgs/04_both-together-v0-v4.jpg}
    \caption{Comparativa de resultados entre \textbf{PV0} (\textbf{BERT}, izquierda) y \textbf{PV3} (Juez \textbf{LLM}, derecha).}
    \label{fig:v0_v3_comparison}
\end{figure}

Estas diferencias metodológicas no son triviales; de hecho, son la clave para entender el fenómeno de la saturación. En la siguiente sección se analizan en detalle las lecciones aprendidas de cada pipeline y cómo sus sesgos inherentes nos condujeron al diseño de un sistema de evaluación más robusto.

\section{Análisis del fenómeno de la saturación de la tarea}
Durante el desarrollo de nuestros pipelines, nos enfrentamos a un fenómeno tan persistente como problemático: la ``saturación de la tarea''. Con este término describimos la tendencia observada de que modelos de IA de diferentes generaciones y capacidades obtuvieran puntuaciones notablemente similares bajo ciertas métricas, creando una aparente meseta de rendimiento que contradecía el rápido avance teórico del campo. Este fenómeno no es una curiosidad, sino un obstáculo fundamental para la correcta valoración del progreso. Entenderlo es entender las trampas de la evaluación de la IA.

Este fenómeno se manifestó de formas distintas pero relacionadas en nuestros pipelines intermedios. Fue como observar un objeto distante a través de diferentes lentes: cada lente corregía una distorsión anterior, pero introducía una nueva, hasta que encontramos la combinación correcta que nos permitió ver con claridad.

\subsection{La distorsión de la rigidez: PV2}
Nuestro primer intento de automatización (\textbf{PV2}) buscaba la objetividad a través de la rigidez de los códigos médicos (\textbf{ICD-10}) y la sinonimia (\textbf{BERT}). El resultado fue un sistema que, si bien era objetivo, era ingenuo. Penalizaba la precisión clínica superior (la ``paradoja del especialista castigado'') y era ciego a cualquier relación que no fuera una equivalencia terminológica. El ranking que producía era claro, pero estaba basado en una visión del mundo clínico excesivamente simplificada. La Figura \ref{fig:pipeline_v2_hist} muestra la distribución de puntuaciones de este sistema: un paisaje de picos discretos, reflejo de su naturaleza binaria, incapaz de capturar los matices.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.5\linewidth]{imgs/03_first-methodology_V2.jpg}
    \caption{Histograma de resultados para \textbf{PV2} (\textbf{ICD10}+\textbf{BERT}).}
    \label{fig:pipeline_v2_hist}
\end{figure}

\subsection{La distorsión de la generosidad: PV3}
Para corregir esta rigidez, \textbf{PV3} empleó un Juez \textbf{LLM}, esperando que su capacidad de razonamiento contextual proporcionara una evaluación más matizada. El resultado fue la manifestación más clara de la saturación. Como se observa en la Figura \ref{fig:v3_hist}, las puntuaciones de todos los modelos se inflaron y se agruparon en una franja muy estrecha en el extremo superior de la escala. Un modelo de una generación anterior como \textbf{o1} obtuvo una puntuación casi idéntica a los de vanguardia como \textbf{o3}.

El motivo de este comportamiento es que el Juez \textbf{LLM}, al evaluar la ``plausibilidad clínica'', se había vuelto un evaluador excesivamente generoso. Entendía las relaciones causa-efecto, las manifestaciones clínicas y las asociaciones diagnósticas, y premiaba todas estas conexiones. Al hacerlo, eliminó la distinción crucial entre una respuesta \textbf{correcta y precisa} y una respuesta meramente \textbf{relevante y plausible}. Esta generosidad actuó como un gran ecualizador, borrando las diferencias de rendimiento y creando una falsa meseta. La tarea para los modelos ya no era ser preciso, sino sonar lo suficientemente convincente para otro \textbf{LLM}.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.5\linewidth]{imgs/031_second-methodology_V2.jpg}
    \caption{Histograma de rendimiento para \textbf{PV3} (Juez \textbf{LLM}), mostrando la saturación de los resultados en la parte alta de la escala.}
    \label{fig:v3_hist}
\end{figure}

La Figura \ref{fig:v2_vs_v3} es la evidencia visual más contundente de este efecto. Muestra la transición de un paisaje de puntuaciones dispersas (\textbf{PV2}) a uno de convergencia casi total (\textbf{PV3}).

\begin{figure}[H]
    \centering
    \includegraphics[width=0.6\linewidth]{imgs/06_icd10bertvsllmasjudgev3.jpg}
    \caption{Comparativa directa de resultados entre el método \textbf{ICD10}+\textbf{BERT} (\textbf{PV2}) y el Juez \textbf{LLM} (\textbf{PV3}).}
    \label{fig:v2_vs_v3}
\end{figure}


\subsection{La naturaleza de la tarea y la naturaleza de los LLM}
La raíz de este fenómeno yace en la interacción de tres factores: la \textbf{definición de la tarea}, la \textbf{naturaleza probabilística de los \textbf{LLM}} y el \textbf{criterio de evaluación}. Nuestra tarea, generar una lista de 5 diagnósticos diferenciales, es fundamentalmente una tarea de recuperación y ranking de información, no de creación desde cero. Los \textbf{LLM} modernos, desde \textbf{o1} hasta \textbf{o3}, poseen bases de conocimiento vastas. Con un prompt claro y restrictivo, todos son capaces de identificar un conjunto de diagnósticos plausibles.

La diferencia entre un modelo bueno y uno excelente no reside tanto en \textit{si} puede encontrar el diagnóstico correcto, sino en \textit{con qué prioridad y confianza} lo presenta. \textbf{PV3}, al ser tan generoso, fallaba en medir esta dimensión de confianza. \textbf{PV4} fue diseñado específicamente para resolver este problema, reintroduciendo la rigidez de forma controlada y haciendo de la \textbf{precisión posicional} un criterio de desempate clave. Al hacerlo, finalmente logramos romper la ilusión de la convergencia y medir lo que realmente importa: no solo el acierto, sino la calidad y confianza de ese acierto.

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
    \caption{Análisis de las relaciones jerárquicas \textbf{ICD-10} en una muestra de los casos, justificando un scoring más sofisticado para \textbf{PV4}.}
    \label{fig:icd10hierarchy}
\end{figure}

\subsection{Lógica operativa y flujo de decisión}
La lógica de \textbf{PV4} es una cascada determinista que evalúa cada una de las 5 propuestas diagnósticas (\textbf{DDX}) de un modelo en orden, desde la posición 1 hasta la 5. El proceso se detiene en cuanto encuentra la primera coincidencia válida con el diagnóstico de referencia (\textbf{GDX}), y la puntuación del caso se determina por la posición de ese primer acierto. Esto prioriza la confianza clínica del modelo.

Para cada \textbf{DDX} individual, el pipeline (Figura \ref{fig:pv4_flowchart}) sigue una jerarquía de validación que va de lo más objetivo a lo más interpretativo:
\begin{enumerate}[leftmargin=*, label=\textbf{Nivel \arabic*:}]
    \item \textbf{Verificación por códigos (máxima objetividad):} Se busca una coincidencia de código \textbf{SNOMED CT} (match exacto). Si no se encuentra, se verifica una coincidencia \textbf{ICD-10} (exacta, padre, hijo o hermano). Si cualquiera de estos métodos tiene éxito, el \textbf{DDX} se considera un acierto, el caso se da por resuelto y se registra su posición.
    \item \textbf{Juicio semántico (red de seguridad):} Solo si los códigos fallan, se recurre al análisis semántico. Primero, se evalúa si la similitud del coseno de \textbf{BERT} supera un umbral de alta confianza ($>0.925$). Si es así, se considera un acierto.
    \item \textbf{Desempate semántico (IA vs. IA):} Si la similitud \textbf{BERT} se encuentra en una zona de incertidumbre ($0.89 < \cos\theta < 0.925$), se activa un juicio competitivo. Se compara el veredicto de \textbf{BERT} con el de un \textbf{Juez LLM}. Si ambos proponen que el \textbf{DDX} es un acierto, se elige aquel que aparezca en la posición más alta de la lista diferencial original, premiando la confianza del modelo. Si solo uno lo aprueba, se acepta ese veredicto. Si ninguno de los dos métodos considera que hay un acierto, el \textbf{DDX} se descarta.
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
    \includegraphics[width=0.9\linewidth]{imgs/v4horizontalstackedbarsbymodelacrossmethods.jpg}
    \caption{Estudio preliminar del desglose de los métodos de resolución del pipeline \textbf{PV4}. Muestra la contribución de cada componente a la validación de aciertos.}
    \label{fig:methods_distribution}
\end{figure}

\subsection{Optimización de prompts y su impacto en el rendimiento}
El benchmark no solo permite comparar modelos, sino también la eficacia de diferentes prompts. La sensibilidad de \textbf{PV4} nos ha permitido cuantificar cómo la estructura del prompt influye en la calidad de la respuesta, mostrando patrones clave para la optimización. Las Figuras \ref{fig:prompt_battle_prompt} y \ref{fig:prompt_battle_model} ilustran la variabilidad del rendimiento en función del prompt utilizado para un mismo modelo y viceversa. En el \textbf{Anexo B} se adjuntan los prompts que obtuvieron los mejores resultados.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.8\linewidth]{imgs/prompt_battle_by_prompt.jpg}
    \caption{Comparativa de rendimiento entre diferentes variantes de prompts (las cruces indican ejecuciones con \textbf{o3} y los círculos con \textbf{4o}).}
    \label{fig:prompt_battle_prompt}
\end{figure}

\begin{figure}[H]
    \centering
    \includegraphics[width=0.8\linewidth]{imgs/prompt_battle_by_model.jpg}
    \caption{Comparativa de rendimiento entre diferentes modelos bajo un mismo prompt (en rojo se muestran los prompts ejecutados con el modelo \textbf{o3}, en azul los de \textbf{4o}; las líneas discontinuas conectan los prompts que se probaron en ambos modelos para visualizar la diferencia de rendimiento).}
    \label{fig:prompt_battle_model}
\end{figure}

Un análisis más detallado sobre el tipo de salida solicitado en el prompt arroja conclusiones significativas:

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

Además del formato de salida, la longitud del prompt es otro factor determinante. El análisis sobre 24 variantes (7 para \textbf{o3} y 17 para \textbf{4o}) muestra que la longitud y la complejidad del output interactúan de forma decisiva. En promedio, añadir 50 palabras a un prompt mejora la tasa de acierto en unos 3 puntos porcentuales. Los prompts cortos (<80 palabras) rinden un 76.1\%, los de longitud media (80-160 palabras) un 86.3\%, y los largos (>160 palabras) un 92.9\%, acumulando una ganancia de hasta 16.8 puntos por longitud. Sin embargo, esta mejora puede verse anulada por la complejidad de la salida. Al controlar la longitud (120-140 palabras), exigir campos adicionales como \texttt{rationale} o \texttt{confidence} provoca una caída de la precisión de hasta 22 puntos porcentuales frente a formatos de salida más simples (p.ej., de 95-97\% a 67-76\%). Esto indica que la penalización por un formato de salida complejo puede pesar más que el beneficio obtenido por un prompt más largo y detallado.

Finalmente, se analizó el efecto de incluir una cláusula "failsafe" en el prompt (p. ej., \textit{"FAILSAFE: If the input is not a clinical case, output []"}). De 24 plantillas, 10 la incluían. La tasa de acierto media para estos prompts fue del 83.1\%, inferior a la media global (86.9\%), sugiriendo una ligera penalización. Esto indica que la validación del tipo de input debería gestionarse mediante un algoritmo previo, más simple y rápido, en lugar de sobrecargar el prompt principal.

\subsection{Ranking final de modelos y análisis comparativo}
Tras la fase de optimización de prompts, se procedió a la evaluación final de los modelos. Los parámetros presentados en la Tabla \ref{tab:final_ranking} son el resultado de un proceso de agregación estadística. Se obtuvieron promediando los resultados de múltiples ejecuciones, filtrando por modelo para obtener estimadores robustos y representativos de su rendimiento general, mitigando así la variabilidad inherente a una única configuración.

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

Los resultados muestran una interesante dicotomía: el modelo \textbf{o3-pro} alcanza la mayor tasa de acierto global (96.4\%), pero es el modelo \textbf{o3} el que demuestra una confianza clínica superior, con la mejor posición promedio (1.474) y el mayor número de aciertos en primera posición (311). La Figura \ref{fig:top_positions} visualiza esta ventaja posicional de \textbf{o3}, que relega el acierto a la última posición con mucha menos frecuencia que sus competidores.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.6\linewidth]{imgs/v4horizontalstackedtoppositions.jpg}
    \caption{Distribución de los aciertos en las Top 5 posiciones por modelo.}
    \label{fig:top_positions}
\end{figure}

\subsubsection{Análisis de estabilidad del rendimiento}
Para profundizar en la robustez de los modelos, se analizó la variabilidad de su rendimiento a través de diferentes prompts. La Tabla \ref{tab:stability} compara directamente \textbf{o3} y \textbf{4o}.

\begin{table}[H]
\centering
\caption{Análisis de estabilidad del rendimiento entre \textbf{o3} y \textbf{4o}.}
\label{tab:stability}
\begin{tabularx}{\linewidth}{Xccc}
\toprule
\textbf{Modelo} & \textbf{Nº Prompts (n)} & \textbf{PPos Media ($\mu \pm \sigma$)} & \textbf{\% Acierto ($\mu \pm \sigma$)} \\ 
\midrule
\textbf{o3} & 7 & 1.474 $\pm$ 0.083 & 93.65\% $\pm$ 2.46 \\
\textbf{4o} & 17 & 1.629 $\pm$ 0.066 & 84.31\% $\pm$ 8.91 \\
\bottomrule
\end{tabularx}
\end{table}

El análisis muestra que el rendimiento de \textbf{o3} no solo es superior en promedio, sino también mucho más estable. Su coeficiente de variación (CV) para la tasa de acierto es de \textbf{0.026}, mientras que el de \textbf{4o} es de \textbf{0.106}. Esto significa que \textbf{la variabilidad de \textbf{4o} cuadruplica la de \textbf{o3}}, lo que lo hace menos predecible y consistente en entornos de producción donde la fiabilidad es crítica.

\subsubsection{Desglose del método de resolución por modelo}
\textbf{PV4} nos permite ver la utilidad validadora de cada modelo. El análisis (Figura \ref{fig:casecount_method}) muestra que \textbf{o3} basa su éxito en una mayor disciplina taxonómica. Por el contrario, \textbf{o3-pro} necesita un mayor apoyo semántico y presenta una cola más larga de aciertos en posiciones tardías (P4-P5), lo que sugiere que obtiene cobertura a costa de la precisión en el ranking.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.9\linewidth]{imgs/v4casecountandaveragepositionbymethod.jpg}
    \caption{Número de casos resueltos y posición promedio por cada método y modelo. Los tonos más oscuros representan mejor puntuación.}
    \label{fig:casecount_method}
\end{figure}

\section{Discusión}
La metodología incremental documentada en este informe nos ha llevado a una conclusión compleja y matizada. Si bien \textbf{PV4} representa nuestro esfuerzo más sofisticado por medir el rendimiento de la IA diagnóstica, sus resultados, lejos de ofrecer una respuesta definitiva, nos enfrentan a una manifestación aún más sutil del fenómeno de la saturación de la tarea.

\subsection{Análisis crítico de los resultados de PV4}
A primera vista, \textbf{PV4} establece una jerarquía clara. Sin embargo, una mirada más crítica muestra un panorama complejo. El modelo \textbf{o3-pro} alcanza la máxima tasa de acierto, pero a costa de una peor priorización y mayor dependencia de la evaluación semántica. Por otro lado, \textbf{o3} emerge como el modelo más confiable y estable, con la mejor posición promedio y la menor variabilidad entre prompts. Esta tensión entre \textbf{cobertura (\textbf{o3-pro}) y confianza (\textbf{o3})} es un hallazgo clave.

La diferencia en la tasa de acierto entre los modelos de alto rendimiento es relativamente estrecha, lo que podría interpretarse como una señal de saturación. Planteamos la siguiente hipótesis: el dataset de 450 casos, a pesar de su diversidad, podría estar concentrado en un espectro de dificultad que se resuelve mediante un "reconocimiento de patrones" altamente sofisticado, más que un "razonamiento de primeros principios". Si la mayoría de los casos se resuelven identificando constelaciones de síntomas que los modelos ya han internalizado masivamente, es lógico que converjan en rendimiento. La tarea no estaría midiendo su capacidad de ``pensar'', sino la exhaustividad de su ``memoria'' de patrones clínicos.

\subsection{Significancia estadística e incertidumbre}
La consistencia de los resultados a través de 450 casos diversos y múltiples variantes de prompts aporta una base empírica razonable para las conclusiones. La ventaja posicional y de estabilidad de \textbf{o3} sobre \textbf{4o} es estadísticamente notable, como demuestra la diferencia de cuatro veces en su coeficiente de variación. De manera similar, la dicotomía entre la tasa de acierto de \textbf{o3-pro} y la calidad del ranking de \textbf{o3} es un patrón robusto. Por tanto, consideramos que la jerarquía y los perfiles de rendimiento observados son señales significativas dentro del marco evaluado, más que artefactos del azar.

En este contexto, \textbf{PV4} ha demostrado tener un poder discriminativo suficiente no solo para rankear modelos, sino para caracterizar sus perfiles de rendimiento (p. ej., estabilidad, confianza vs. cobertura) y para guiar la ingeniería de prompts.

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
    \includegraphics[width=0.8\linewidth]{imgs/08_etl_visualized_as_sankey_at_20250708.png}
    \caption{Diagrama de Sankey que visualiza el proceso de ETL para la composición del dataset de evaluación de 450 casos a partir de las fuentes originales.}
    \label{fig:sankey_appendix}
\end{figure}

\newpage
\section{Prompts con mayor rendimiento}
\label{app:prompts}
A continuación se presentan los prompts que obtuvieron los mejores resultados para los modelos \textbf{o3} y \textbf{4o}, junto con sus puntuaciones de rendimiento (posición promedio y tasa de acierto).

\subsection{Mejores prompts para \textbf{o3} (TOP4)}

\subsubsection*{diagnosis\_description\_symptoms\_classic\_v2}
\textbf{Puntuación: 1.326 - 92.7\%}
\begin{verbatim}
You are a diagnostic assistant. Given the patient case below, generate N possible diagnoses. For each:

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

\subsubsection*{diagnosis\_description\_symptoms\_classic\_v4}
\textbf{Puntuación: 1.422 - 90.7\%}
\begin{verbatim}
You are a diagnostic assistant. Given the patient case below, generate N possible diagnoses. For each:

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

\subsubsection*{juanjo\_v1 (original)}
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

\subsubsection*{\textit{diagnosis\_description\_symptoms\_classic\_v2}}
\textit{Este prompt, ya presentado en la sección anterior, también obtiene el mejor rendimiento para el modelo \textbf{4o}.}

\subsubsection*{juanjo\_v1 (sin \texttt{description})}
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