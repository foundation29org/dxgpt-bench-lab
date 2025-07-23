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
\usepackage{appendix}
\usepackage{tikz}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning}
\usepackage{verbatim}
\usepackage{makecell}
\usepackage{longtable} % Para el glosario

% --- CONFIGURACIÓN DE PÁGINA Y ESTILO ---
\geometry{a4paper, margin=2.5cm}
\setlength{\headheight}{14.5pt}

\definecolor{primarycolor}{RGB}{0, 51, 102}
\definecolor{graytext}{RGB}{80, 80, 80}

\hypersetup{colorlinks=true, linkcolor=primarycolor, urlcolor=primarycolor, citecolor=primarycolor}

\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\nouppercase{\leftmark}}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0pt}
\fancypagestyle{plain}{\fancyhf{}}

% --- FORMATO DE TÍTULOS (Sentence case) ---
\titleformat{\section}{\normalfont\Large\bfseries\color{primarycolor}}{\thesection.}{1em}{}
\titlespacing*{\section}{0pt}{3.5ex plus 1ex minus .2ex}{2.3ex plus .2ex}

\titleformat{\subsection}{\normalfont\large\bfseries\color{graytext}}{\thesubsection}{1em}{}
\titlespacing*{\subsection}{0pt}{3.25ex plus 1ex minus .2ex}{1.5ex plus .2ex}

% --- Colores y estilos para el diagrama simplificado ---
\definecolor{snomed}{RGB}{217, 234, 211}
\definecolor{icd}{RGB}{252, 229, 205}
\definecolor{bert}{RGB}{214, 234, 248}
\definecolor{llm}{RGB}{235, 222, 240}
\tikzset{
    proc/.style={rectangle, rounded corners, draw=black, thick, minimum height=1.2cm, minimum width=2.8cm, text centered, font=\small, align=center},
    dec/.style={diamond, draw=black, thick, aspect=1.8, minimum size=1.5cm, text centered, font=\small},
    out/.style={ellipse, draw=primarycolor, thick, minimum height=1cm, minimum width=2cm, text centered, font=\small\bfseries},
    line/.style={-Stealth, thick, draw=graytext}
}

% --- DOCUMENTO ---
\begin{document}

% --- PÁGINA DE TÍTULO ---
\begin{titlepage}
    \centering
    \vspace*{2cm}
    
    {\Huge\bfseries\color{primarycolor} Evaluación jerárquica de modelos de lenguaje en diagnóstico clínico: superando la saturación mediante un pipeline multicapas (simplificado)}
    
    \vspace{1.5cm}
    
    {\Large\bfseries Análisis metodológico de PV0-PV4}
    
    \vspace{2.5cm}
    
    \begin{flushleft}
    \large
    \begin{tabular}{@{}l}
        \textbf{Autores:} Yago Mendoza, Javier Logroño\\
        \textbf{Institución:} Foundation 29 \\
        \textbf{Fecha:} \today \\
        \textbf{Versión del Documento:} 1.0 \\
    \end{tabular}
    \end{flushleft}
    
    \vfill
    
    \textit{\small Este documento presenta un resumen de los hallazgos y la evolución de los marcos de evaluación para la herramienta de diagnóstico asistido por IA DxGPT, destinado a un público no especializado en el ámbito técnico.}
    
\end{titlepage}
\newpage

% --- GLOSARIO DE TÉRMINOS (CORREGIDO) ---
\section*{Glosario de términos}
\begin{longtable}{@{} >{\small\bfseries}p{0.3\linewidth} p{0.65\linewidth}@{}}
\toprule
Término & Descripción simplificada \\
\midrule
\endhead
\bottomrule
\endfoot
\endlastfoot
LLM (Large Language Model) & Un modelo de inteligencia artificial avanzado, entrenado con enormes cantidades de texto para comprender, resumir, generar y predecir contenido. Es la tecnología base de herramientas como ChatGPT. \\
\addlinespace
Pipeline de evaluación & Una secuencia de pasos o un flujo de trabajo automatizado diseñado para medir el rendimiento de los modelos de IA de forma sistemática y reproducible. \\
\addlinespace
Juez-IA (LLM as a Judge) & El uso de un LLM muy avanzado para evaluar y puntuar las respuestas de otros modelos de IA, basándose en su comprensión del contexto y la lógica. \\
\addlinespace
Sistema de supervisión semántica (BERT) & Un componente de IA especializado en determinar la similitud de significado entre dos textos, incluso si no usan las mismas palabras. Evalúa si dos diagnósticos son conceptualmente equivalentes. \\
\addlinespace
ICD-10 / SNOMED CT & Sistemas de codificación médica estándar utilizados a nivel internacional para clasificar enfermedades y procedimientos. Proporcionan una base objetiva para comparar diagnósticos. \\
\addlinespace
Posición en la lista (P1, P5, etc.) & La posición en la que aparece el diagnóstico correcto dentro de la lista de 5 propuestas generadas por el modelo. Una posición baja (ej. P1) indica una mayor "confianza clínica" del modelo. \\
\addlinespace
PV0, PV2, PV3, PV4 & Versiones sucesivas de nuestro pipeline de evaluación. Cada versión fue un intento de mejorar la anterior, culminando en PV4, el sistema final y más robusto. \\
\end{longtable}
\newpage

\begin{center}
    {\Large \textbf{Resumen}}\\[1em]
\end{center}
Este informe describe la evolución de nuestros métodos para evaluar cuatro modelos de lenguaje de OpenAI sobre \textbf{450 casos pediátricos}. El análisis inicial reveló que los sistemas de evaluación simples generaban resultados engañosos. Un método basado en códigos médicos penalizaba diagnósticos muy precisos, mientras que un evaluador basado en una IA (un "Juez-IA") tendía a valorar todas las respuestas como buenas si eran plausibles, ocultando las diferencias reales de rendimiento entre los modelos.

Para solucionar esto, desarrollamos \textbf{PV4}, un sistema de evaluación avanzado que combina la \textbf{objetividad de los códigos médicos} con el \textbf{juicio contextual de una IA}. Además, introdujimos una métrica clave: \textbf{la posición del diagnóstico correcto en la lista de propuestas}, como un indicador de la confianza del modelo.

Esta nueva metodología reveló una jerarquía de rendimiento clara. El modelo \textbf{o3} emergió como el \textbf{más fiable y estable}, con la mejor posición promedio y el mayor número de aciertos en primer lugar. Aunque el modelo \textbf{o3-pro} obtuvo una tasa de aciertos brutos ligeramente superior, lo hizo a costa de una peor priorización de sus diagnósticos. En resumen, la calidad de la evaluación es tan importante como la calidad del modelo evaluado para obtener una visión precisa de sus capacidades.

\section{Planteamiento del problema de evaluación}

La validación de sistemas de IA para el soporte al diagnóstico clínico es un desafío crucial. No se trata simplemente de verificar si una IA "acierta", sino de evaluar la calidad, robustez y relevancia clínica de su razonamiento. Una hipótesis diagnóstica que suena plausible pero no es precisa puede comprometer la seguridad del paciente y la confianza del profesional.

Nuestro objetivo es establecer un marco de evaluación que vaya más allá de métricas superficiales y permita discernir con claridad el rendimiento real entre diferentes modelos de IA. Esta evaluación debe capturar no solo el acierto, sino también la priorización y la precisión de las propuestas diagnósticas. Este informe documenta el proceso que hemos seguido para construir dicho marco, aprendiendo tanto sobre los modelos como sobre nuestras propias herramientas de medición a partir de un dataset diverso (cuya composición se detalla en el \textbf{Anexo A}).

\section{Evolución hacia un sistema de evaluación robusto}

Para encontrar la mejor manera de medir el rendimiento de los modelos, desarrollamos una serie de "pipelines" o flujos de trabajo de evaluación. Cada uno corregía los defectos del anterior, llevándonos a un sistema final mucho más fiable.

La Tabla \ref{tab:pipeline_evolution} resume este viaje metodológico. Esta progresión es la clave para entender por qué fue necesario desarrollar un sistema tan sofisticado como PV4. Es crucial entender que PV0, PV2 y PV3 fueron etapas de aprendizaje que nos permitieron identificar sesgos y limitaciones. \textbf{El único sistema válido y utilizado para los resultados finales es PV4}.

\begin{table}[H]
    \centering
    \caption{Evolución de los pipelines de evaluación: de la simplicidad a la robustez.}
    \label{tab:pipeline_evolution}
    \renewcommand{\arraystretch}{1.5} 
    \begin{tabularx}{\linewidth}{@{} >{\bfseries}c X X X @{}}
        \toprule
        \textbf{Pipeline} & \textbf{Ventajas} & \textbf{Inconvenientes} & \textbf{Lección aprendida} \\
        \midrule
        \makecell{\textbf{PV0}} & 
        Simple y rápido. &
        Ciego al contexto clínico. Confundía similitud de palabras con relevancia diagnóstica. & 
        La similitud textual por sí sola es una métrica engañosa. \\
        \midrule
        \makecell{\textbf{PV2}} &
        Introduce objetividad usando códigos médicos estándar. &
        Demasiado rígido. Penalizaba respuestas correctas pero más específicas que el diagnóstico de referencia. &
        La codificación estricta no captura la flexibilidad del lenguaje clínico. \\
        \midrule
        \makecell{\textbf{PV3}} &
        Un "Juez-IA" que entiende el contexto y los matices clínicos. &
        Demasiado "generoso". Hacía que todos los modelos parecieran igual de buenos, ocultando diferencias. &
        Un juicio puramente contextual premia la plausibilidad, no la precisión. \\
        \midrule
        \makecell{\textbf{PV4}} &
        \textbf{Equilibra la objetividad de los códigos con la flexibilidad del juicio de IA}. Usa la posición como métrica de confianza. &
        Mayor complejidad interna. &
        La evaluación de alta fidelidad exige combinar objetividad, contexto y prioridad. \\
        \bottomrule
    \end{tabularx}
\end{table}

Los pipelines intermedios sufrían de "saturación de la tarea": un fenómeno donde modelos de distinta calidad parecían rendir igual. Los sistemas rígidos (PV2) castigaban la precisión, y los sistemas flexibles (PV3) eran demasiado generosos, premiando la plausibilidad en lugar de la exactitud. Esto nos obligó a diseñar un sistema híbrido que superara ambas limitaciones.

\section{Lógica operativa de PV4: un sistema jerárquico}

PV4 es el resultado de este aprendizaje. Es un sistema jerárquico que combina la objetividad de los códigos con la inteligencia del análisis contextual. Su principio fundamental es evaluar las 5 propuestas diagnósticas de un modelo en orden (de la 1 a la 5) y \textbf{detenerse en cuanto encuentra el primer acierto válido}. La puntuación del caso se basa en la posición de ese primer acierto, premiando así la confianza clínica del modelo.

El flujo de decisión para cada diagnóstico propuesto, como se muestra en la Figura \ref{fig:pv4_flowchart}, sigue una cascada de lo más objetivo a lo más interpretativo:

\begin{enumerate}[leftmargin=*, label=\textbf{Paso \arabic*:}]
    \item \textbf{Verificación por códigos médicos.} Primero, el sistema busca una coincidencia objetiva usando las clasificaciones estándar \textbf{SNOMED} e \textbf{ICD-10}. Si se encuentra una coincidencia directa o jerárquicamente cercana (ej. un sub-diagnóstico), la propuesta se valida y el proceso termina.

    \item \textbf{Supervisión semántica.} Si no hay coincidencia de código, un \textbf{sistema de supervisión semántica} comprueba si el diagnóstico propuesto es conceptualmente equivalente al correcto, aunque se escriba con palabras diferentes.

    \item \textbf{Juicio de una IA experta.} Si los pasos anteriores fallan o generan dudas, se recurre a un \textbf{Juez-IA} (un modelo de lenguaje avanzado) para que realice una evaluación contextual final y determine si la propuesta es clínicamente válida.
\end{enumerate}

\begin{figure}[H]
    \centering
    \begin{tikzpicture}[node distance=1.5cm and 1cm, scale=0.85, transform shape]
    % --- NODOS ---
    \node (in)   [proc] {\textbf{Diagnóstico} \\ \textbf{Propuesto}};
    \node (sno)  [proc, below=of in, fill=snomed!25] {Paso 1: ¿Coincide el \\ código \textbf{SNOMED}?};
    \node (icd)  [proc, below=of sno, fill=icd!20] {Paso 1: ¿Coincide el \\ código \textbf{ICD-10}?};
    \node (bert) [proc, below=of icd, fill=bert!20] {Paso 2: ¿Es un \\ \textbf{sinónimo clínico}?};
    \node (llm)  [proc, below=of bert, fill=llm!20] {Paso 3: ¿Es válido \\ según el \textbf{Juez-IA}?};
    \node (out)  [out, right=2.5cm of icd, yshift=-1cm] {Acierto};
    \node (fail) [out, below=of llm, fill=gray!30, draw=graytext] {Fallo};

    % --- ARISTAS ---
    \draw[line] (in)   -- (sno);
    \draw[line] (sno)  -- node[midway, right, xshift=2mm] {\footnotesize No} (icd);
    \draw[line] (icd)  -- node[midway, right, xshift=2mm] {\footnotesize No} (bert);
    \draw[line] (bert) -- node[midway, right, xshift=2mm] {\footnotesize No} (llm);
    \draw[line] (llm) -- node[midway, right, xshift=2mm] {\footnotesize No} (fail);

    % Salidas de acierto
    \draw[line] (sno.east) -| node[very near start, above] {\footnotesize Sí} (out.north);
    \draw[line] (icd.east) -- node[midway, above] {\footnotesize Sí} (out.west);
    \draw[line] (bert.east) -| node[very near start, above] {\footnotesize Sí} (out.south);
    \draw[line] (llm.east) -| node[very near start, above] {\footnotesize Sí} (out.south);
    \end{tikzpicture}
    \caption{Diagrama de flujo simplificado del proceso de evaluación de \textbf{PV4} para un único diagnóstico propuesto.}
    \label{fig:pv4_flowchart}
\end{figure}

\section{Resultados y ranking final de modelos}

La aplicación del pipeline PV4 nos permitió discriminar el rendimiento de los modelos con alta precisión. La Tabla \ref{tab:final_ranking} muestra los resultados finales. Aunque \textbf{o3-pro} tiene la tasa de acierto global más alta, \textbf{o3} demuestra ser el modelo más \textbf{confiable}: obtiene la mejor posición promedio y acierta en primer lugar con mayor frecuencia.

\begin{table}[H]
\centering
\caption{Ranking y métricas clave de rendimiento por modelo (pipeline \textbf{PV4}).}
\label{tab:final_ranking}
\begin{tabularx}{\linewidth}{lXXXX}
\toprule
\textbf{Métrica} & \textbf{o3} & \textbf{o1} & \textbf{o3-pro} & \textbf{4o} \\
\midrule
\textbf{Tasa de acierto (\%)} & 93.7\% & 91.4\% & \textbf{96.4\%} & 94.3\% \\
\textbf{Posición promedio} & \textbf{1,47} & 1,59 & 1,60 & 1,63 \\
Aciertos en posición 1 (P1) & \textbf{311} & 305 & 299 & 299 \\
Aciertos en posición 5 (P5) & \textbf{9} & 17 & 24 & 20 \\
\bottomrule
\end{tabularx}
\end{table}

La Figura \ref{fig:top_positions} visualiza esta diferencia clave. Muestra cómo \textbf{o3} concentra la mayoría de sus aciertos en las primeras posiciones, mientras que otros modelos, aunque aciertan, lo hacen con menor prioridad. Esta capacidad de priorizar correctamente es fundamental para la utilidad clínica. Análisis más detallados sobre la estabilidad de los modelos y el desglose de métodos se encuentran en el \textbf{Anexo B}.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.7\linewidth]{imgs/v4horizontalstackedtoppositions.jpg}
    \caption{Distribución de los aciertos en las Top 5 posiciones por modelo. \textbf{o3} destaca por su alta concentración de aciertos en primera posición (P1).}
    \label{fig:top_positions}
\end{figure}


\section{Conclusiones}

El diseño de un sistema de evaluación robusto es tan importante como el desarrollo de los propios modelos de IA. Nuestro proceso iterativo nos ha llevado a las siguientes conclusiones:

\medskip
\noindent\textbf{Veredicto del rendimiento de los modelos}
\begin{itemize}[nosep]
    \item \textbf{o3} destaca por su \textbf{fiabilidad}: obtiene la mejor posición promedio (1,47) y el mayor número de aciertos en primera posición, lo que indica una mayor confianza clínica.
    \item \textbf{o3-pro} logra la \textbf{máxima cobertura} (96,4\% de aciertos) pero a costa de una peor priorización en su lista de diagnósticos diferenciales.
    \item La estabilidad de \textbf{o3} fue notablemente superior a la de otros modelos como \textbf{4o}, haciéndolo más predecible y consistente para un uso práctico.
\end{itemize}

\medskip
\noindent\textbf{Lecciones sobre la metodología de evaluación}
\begin{itemize}[nosep]
    \item Los sistemas de evaluación simples pueden ser engañosos. La rigidez de los códigos (PV2) castiga la especificidad, mientras que la flexibilidad de un Juez-IA (PV3) oculta las diferencias de rendimiento.
    \item La mejor aproximación es un \textbf{sistema híbrido y jerárquico (PV4)} que combina la objetividad de los códigos con el juicio contextual, utilizando la \textbf{posición en la lista} como un indicador clave de la confianza del modelo.
    \item El evaluador no es un observador pasivo; su diseño define activamente qué se considera un "buen" rendimiento.
\end{itemize}

\newpage
\begin{appendices}

\section{Composición del dataset de evaluación}
El dataset final de 450 casos se construyó a partir de un universo de 9.677 casos clínicos. El siguiente diagrama de Sankey (Figura \ref{fig:sankey_appendix}) visualiza el flujo de Extracción, Transformación y Carga (ETL) que garantiza la diversidad y representatividad del conjunto de pruebas.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.8\linewidth]{imgs/08_etl_visualized_as_sankey_at_20250708.png}
    \caption{Diagrama de Sankey que visualiza el proceso de ETL para la composición del dataset de evaluación.}
    \label{fig:sankey_appendix}
\end{figure}

\section{Figuras y tablas adicionales}

\begin{figure}[H]
    \centering
    \includegraphics[width=0.9\linewidth]{imgs/00_all_450_diversity_visualized.jpeg}
    \caption{Distribución de los 450 casos clínicos por capítulos de la codificación \textbf{ICD-10}.}
\end{figure}

\begin{figure}[H]
    \centering
    \includegraphics[width=0.9\linewidth]{imgs/v4casecountandaveragepositionbymethod.jpg}
    \caption{Número de casos resueltos y posición promedio por cada método del pipeline \textbf{PV4}. Los tonos más oscuros representan mejor puntuación (posición más baja).}
\end{figure}

\begin{figure}[H]
    \centering
    \includegraphics[width=0.8\linewidth]{imgs/prompt_battle_by_prompt.jpg}
    \caption{Comparativa de rendimiento entre diferentes variantes de prompts (las cruces indican ejecuciones con \textbf{o3} y los círculos con \textbf{4o}).}
\end{figure}

\begin{table}[H]
\centering
\caption{Análisis de estabilidad del rendimiento entre \textbf{o3} y \textbf{4o}.}
\label{tab:stability}
\begin{tabularx}{\linewidth}{Xccc}
\toprule
\textbf{Modelo} & \textbf{Nº prompts (n)} & \textbf{PPos media ($\mu \pm \sigma$)} & \textbf{\% acierto ($\mu \pm \sigma$)} \\ 
\midrule
\textbf{o3} & 7 & 1.474 $\pm$ 0.083 & 93.65\% $\pm$ 2.46 \\
\textbf{4o} & 17 & 1.629 $\pm$ 0.066 & 84.31\% $\pm$ 8.91 \\
\bottomrule
\end{tabularx}
\end{table}

\newpage
\section{Prompts de alto rendimiento}
\label{app:prompts}
A continuación se presentan los prompts que obtuvieron los mejores resultados para los modelos \textbf{o3} y \textbf{4o}, junto con sus puntuaciones de rendimiento (posición promedio y tasa de acierto).

\subsection{Mejores prompts para o3 (TOP4)}

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

\subsection{Mejores prompts para 4o (TOP4)}

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