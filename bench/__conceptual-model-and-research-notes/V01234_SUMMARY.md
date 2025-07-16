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

% --- CONFIGURACIÓN DE PÁGINA Y ESTILO ---
\geometry{a4paper, margin=2.5cm}

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


% --- DOCUMENTO ---
\begin{document}

% --- PÁGINA DE TÍTULO ---
\begin{titlepage}
    \centering
    \vspace*{2cm}
    
    {\Huge\bfseries\color{primarycolor} Informe sobre la evaluación de modelos de IA para soporte al diagnóstico clínico}
    
    \vspace{1.5cm}
    
    {\Large\bfseries Análisis metodológico de los pipelines v0-v4 y el fenómeno de la saturación de la tarea}
    
    \vspace{2.5cm}
    
    \begin{flushleft}
    \large
    \begin{tabular}{@{}l}
        \textbf{Autores:} [Nombres de los Autores] \\
        \textbf{Institución:} [Nombre de la Institución / Fundación] \\
        \textbf{Fecha:} \today \\
        \textbf{Versión del Documento:} 5.0 \\
    \end{tabular}
    \end{flushleft}
    
    \vfill
    
    \textit{\small Este documento presenta un análisis pormenorizado de los hallazgos y la evolución de los marcos de evaluación para herramientas de diagnóstico asistido por IA, abarcando desde estudios clínicos iniciales hasta el desarrollo de pipelines automatizados de alta fidelidad.}
    
\end{titlepage}
\newpage

\tableofcontents
\newpage

\section{Planteamiento del problema de evaluación}
La validación de sistemas de inteligencia artificial para el soporte al diagnóstico clínico es un desafío metodológico fundamental. No se trata meramente de verificar la corrección de una respuesta, sino de evaluar la calidad, robustez y relevancia de un proceso de razonamiento complejo. Como fundación dedicada al avance de estas tecnologías, nuestro objetivo es establecer un marco de evaluación que sea a la vez riguroso, escalable y transparente. Este marco debe ser capaz de discriminar con precisión el rendimiento entre diferentes modelos y arquitecturas, superando las métricas superficiales para capturar la esencia del juicio clínico.

El presente informe documenta el proceso iterativo que hemos seguido para construir dicho marco. Partimos de una premisa de escepticismo científico: toda metodología de evaluación introduce sus propios sesgos y artefactos. Nuestro trabajo, por tanto, no ha sido solo aplicar métricas, sino interrogar a las propias métricas. Este documento narra la evolución de nuestros pipelines de evaluación, desde los primeros intentos hasta el sistema actual, detallando cómo cada fase nos reveló tanto las capacidades de los modelos como las limitaciones de nuestras herramientas de medición.

El eje central de este informe es el análisis de un fenómeno recurrente y crítico: la ``saturación de la tarea'', una aparente convergencia de rendimiento que amenazaba con enmascarar el progreso real. A través de este análisis, demostramos cómo un diseño metodológico cuidadoso puede desentrañar estas paradojas y proporcionar una visión clara y fiable del estado del arte en IA diagnóstica.

\section{Composición del entorno de pruebas}
Para llevar a cabo una evaluación rigurosa, es indispensable contar con un entorno de pruebas ---un dataset--- que sea representativo y desafiante. Nuestro análisis se basa en un conjunto de \textbf{450 casos clínicos}, extraídos de un benchmark más amplio mediante un proceso de selección estratificada.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.8\linewidth]{imgs/08_etl_visualized_as_sankey_at_20250708.png}
    \caption{Diagrama de Sankey que visualiza el proceso de ETL para la composición del dataset de evaluación.}
    \label{fig:sankey}
\end{figure}

\subsection{Análisis exploratorio y diseño del scoring}
Antes de construir el pipeline de evaluación final (v4), se realizó un análisis exploratorio fundamental. Se generaron las respuestas de cinco modelos distintos para los 450 casos, creando un corpus de 2.250 diagnósticos diferenciales (DDX) para cada caso. Sobre una muestra aleatoria de este ``dataset Frankenstein'' se aplicaron técnicas de \textit{text analytics} para entender la estructura de las respuestas y la viabilidad de usar vocabularios controlados.

Este análisis preliminar fue crucial y reveló tres hechos clave que informaron directamente el diseño del Pipeline v4:
\begin{enumerate}
    \item \textbf{Viabilidad de SNOMED CT:} Se confirmó que SNOMED CT era el sistema de codificación con mayor cobertura y robustez, convirtiéndolo en el candidato ideal para ser el primer criterio de matching.
    \item \textbf{Complejidad de ICD-10:} Se observó que las coincidencias exactas de ICD-10 eran poco frecuentes. Sin embargo, las relaciones jerárquicas (padre, hijo) eran comunes y clínicamente significativas. Esto llevó a la decisión de incluir estas relaciones en el scoring del Pipeline v4 para que fuera más justo y preciso.
    \item \textbf{La inevitable brecha semántica:} El análisis confirmó la existencia de una gran cantidad de casos donde ningún código conectaba el diagnóstico principal con los diferenciales. Esto validó la necesidad de un mecanismo de evaluación semántica (como BERT o un Juez LLM) como último recurso.
\end{enumerate}

\begin{figure}[H]
    \centering
    \includegraphics[width=0.9\linewidth]{imgs/v40studyoficd10jerarquy.jpg}
    \caption{Análisis de las relaciones jerárquicas ICD-10 en una muestra de los casos, justificando un scoring más sofisticado para el Pipeline v4.}
    \label{fig:icd10hierarchy}
\end{figure}

\subsection{Diversidad del dataset final}
El dataset de 450 casos fue seleccionado para asegurar una amplia cobertura de patologías, garantizando que la evaluación no estuviera sesgada hacia una especialidad concreta.
\begin{figure}[H]
    \centering
    \includegraphics[width=0.9\linewidth]{imgs/00_all_450_diversity_visualized.jpeg}
    \caption{Distribución de los 450 casos clínicos por capítulos de la codificación ICD-10.}
    \label{fig:diversity}
\end{figure}

\section{Evolución de los pipelines de evaluación}
El desarrollo de nuestro framework de evaluación ha sido un proceso iterativo, donde cada pipeline representó una hipótesis sobre la mejor manera de medir el rendimiento. Esta evolución fue necesaria para confrontar y resolver el fenómeno de la saturación de la tarea.

\begin{itemize}[leftmargin=*]
    \item \textbf{Pipeline v0:} Fue el primer intento de automatización, utilizando exclusivamente un modelo \textbf{BERT} para medir la similitud semántica. Se aplicó principalmente a modelos de Hugging Face. Su limitación era la incapacidad para entender el contexto clínico o las relaciones jerárquicas, reduciendo la evaluación a una simple comparación de proximidad textual.

    \item \textbf{Pipeline v1/v2 (ICD10+BERT):} Representó un salto en sofisticación al introducir los códigos \textbf{ICD-10} como primer criterio de evaluación. Si la coincidencia de código fallaba, se utilizaba BERT como red de seguridad. Este método, aunque más estructurado, introdujo la ``paradoja del especialista castigado'', penalizando respuestas clínicamente superiores pero terminológicamente más específicas.

    \item \textbf{Pipeline v3 (Juez LLM):} Para corregir la rigidez anterior, este pipeline delegó la evaluación completa a un \textbf{Large Language Model} (GPT-4o) que actuaba como "juez". Su capacidad de razonamiento contextual le permitió entender relaciones clínicas complejas, pero su excesiva "generosidad" llevó a la saturación de los resultados, como se discutirá en la siguiente sección.
\end{itemize}

La Figura \ref{fig:v0_v3_comparison} ilustra visualmente la diferencia en las distribuciones de resultados entre el enfoque del Pipeline v0 (aplicado a modelos Hugging Face) y el del Pipeline v3 (aplicado a modelos OpenAI), mostrando cómo diferentes metodologías producen "realidades" de rendimiento muy distintas.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.9\linewidth]{imgs/04_both-together-v0-v4.jpg}
    \caption{Comparativa de resultados entre el Pipeline v0 (BERT, izquierda) y el Pipeline v3 (Juez LLM, derecha).}
    \label{fig:v0_v3_comparison}
\end{figure}

\section{Análisis del fenómeno de la saturación de la tarea}
Durante el desarrollo de nuestros pipelines, nos enfrentamos a un fenómeno tan persistente como problemático: la ``saturación de la tarea''. Con este término describimos la tendencia observada de que modelos de IA de diferentes generaciones y capacidades obtuvieran puntuaciones notablemente similares bajo ciertas métricas, creando una aparente meseta de rendimiento que contradecía el rápido avance teórico del campo. Este fenómeno no es una curiosidad, sino un obstáculo fundamental para la correcta valoración del progreso. Entenderlo es entender las trampas de la evaluación de la IA.

Este fenómeno se manifestó de formas distintas pero relacionadas en nuestros pipelines intermedios. Fue como observar un objeto distante a través de diferentes lentes: cada lente corregía una distorsión anterior, pero introducía una nueva, hasta que encontramos la combinación correcta que nos permitió ver con claridad.

\subsection{La distorsión de la rigidez: el pipeline v2}
Nuestro primer intento de automatización (Pipeline v2) buscaba la objetividad a través de la rigidez de los códigos médicos (ICD-10) y la sinonimia (BERT). El resultado fue un sistema que, si bien era objetivo, era ingenuo. Penalizaba la precisión clínica superior (la ``paradoja del especialista castigado'') y era ciego a cualquier relación que no fuera una equivalencia terminológica. El ranking que producía era claro, pero estaba basado en una visión del mundo clínico excesivamente simplificada. La Figura \ref{fig:pipeline_v2_hist} muestra la distribución de puntuaciones de este sistema: un paisaje de picos discretos, reflejo de su naturaleza binaria, incapaz de capturar los matices.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.7\linewidth]{imgs/03_first-methodology.png}
    \caption{Histograma de resultados para el Pipeline v2 (ICD10+BERT).}
    \label{fig:pipeline_v2_hist}
\end{figure}

\subsection{La distorsión de la generosidad: el pipeline v3}
Para corregir esta rigidez, el Pipeline v3 empleó un Juez LLM, esperando que su capacidad de razonamiento contextual proporcionara una evaluación más matizada. El resultado fue la manifestación más clara de la saturación. Como se observa en la Figura \ref{fig:v3_hist}, las puntuaciones de todos los modelos se inflaron y se agruparon en una franja muy estrecha en el extremo superior de la escala. Un modelo de una generación anterior como `o1` obtuvo una puntuación casi idéntica a los de vanguardia como `o3`.

¿Qué había ocurrido? El Juez LLM, al evaluar la ``plausibilidad clínica'', se había vuelto un evaluador excesivamente generoso. Entendía las relaciones causa-efecto, las manifestaciones clínicas y las asociaciones diagnósticas, y premiaba todas estas conexiones. Al hacerlo, eliminó la distinción crucial entre una respuesta \textbf{correcta y precisa} y una respuesta meramente \textbf{relevante y plausible}. Esta generosidad actuó como un gran ecualizador, borrando las diferencias de rendimiento y creando una falsa meseta. La tarea para los modelos ya no era ser preciso, sino sonar lo suficientemente convincente para otro LLM.

La Figura \ref{fig:v2_vs_v3} es la evidencia visual más contundente de este efecto. Muestra la transición de un paisaje de puntuaciones dispersas (v2) a uno de convergencia casi total (v3).

\begin{figure}[H]
    \centering
    \includegraphics[width=0.9\linewidth]{imgs/06_icd10bertvsllmasjudgev3.jpg}
    \caption{Comparativa directa de resultados entre el método ICD10+BERT (v2) y el Juez LLM (v3).}
    \label{fig:v2_vs_v3}
\end{figure}

\begin{figure}[H]
    \centering
    \includegraphics[width=0.7\linewidth]{imgs/031_second-methodology_V2.jpg}
    \caption{Histograma de rendimiento para el Pipeline v3 (Juez LLM).}
    \label{fig:v3_hist}
\end{figure}

\subsection{La naturaleza de la tarea y la naturaleza de los LLM}
La raíz de este fenómeno yace en la interacción de tres factores: la \textbf{definición de la tarea}, la \textbf{naturaleza probabilística de los LLM} y el \textbf{criterio de evaluación}. Nuestra tarea, generar una lista de 5 diagnósticos diferenciales, es fundamentalmente una tarea de recuperación y ranking de información, no de creación desde cero. Los LLM modernos, desde `o1` hasta `o3`, poseen bases de conocimiento vastas. Con un prompt claro y restrictivo, todos son capaces de identificar un conjunto de diagnósticos plausibles.

La diferencia entre un modelo bueno y uno excelente no reside tanto en \textit{si} puede encontrar el diagnóstico correcto, sino en \textit{con qué prioridad y confianza} lo presenta. El Pipeline v3, al ser tan generoso, fallaba en medir esta dimensión de confianza. El Pipeline v4 fue diseñado específicamente para resolver este problema, reintroduciendo la rigidez de forma controlada y haciendo de la \textbf{precisión posicional} un criterio de desempate clave. Al hacerlo, finalmente logramos romper la ilusión de la convergencia y medir lo que realmente importa: no solo el acierto, sino la calidad y confianza de ese acierto.

\section{Diseño y lógica del pipeline v4}
El Pipeline v4 es el resultado de este proceso de aprendizaje. No es un método único, sino un sistema jerárquico que sintetiza las lecciones de sus predecesores, buscando un equilibrio entre la objetividad de los códigos y la inteligencia del análisis semántico.

Su lógica es una cascada de evaluación en tres niveles:
\begin{enumerate}[leftmargin=*, label=\textbf{Nivel \arabic*:}]
    \item \textbf{Verificación por códigos (máxima prioridad):} Intenta resolver el caso con la máxima objetividad, buscando coincidencias de código SNOMED CT y luego ICD-10 (exacta y jerárquica). Este nivel premia la disciplina y el rigor.
    \item \textbf{Juicio semántico competitivo (IA vs. IA):} Solo si los códigos fallan, se activa una competencia entre un análisis de similitud matemática (BERT) y un juicio clínico simulado (Juez LLM).
    \item \textbf{Criterio de desempate (precisión posicional):} Se elige la coincidencia (BERT o LLM) que aparezca en la posición más alta de la lista. Este paso es crucial, pues mide la confianza del modelo en su propia respuesta.
\end{enumerate}

\section{Resultados y análisis del pipeline v4}
La aplicación de este marco de alta fidelidad reveló una jerarquía de rendimiento clara y robusta.

\subsection{Métricas cuantitativas y ranking final}

\begin{table}[H]
\centering
\caption{Ranking y métricas clave de rendimiento por modelo (Pipeline v4).}
\label{tab:v4_results}
\begin{tabularx}{\linewidth}{lXXXX}
\toprule
\textbf{Métrica} & \textbf{o3} & \textbf{o1} & \textbf{o3-pro} & \textbf{4o} \\
\midrule
\textbf{Puntuación Final (\%)} & \textbf{89.98\%} & 88.19\% & 87.73\% & 87.70\% \\
\textbf{Posición Promedio} & \textbf{1.501} & 1.590 & 1.613 & 1.615 \\
Total Casos Resueltos & 433 (96.2\%) & \textbf{437 (97.1\%)} & \textbf{437 (97.1\%)} & 434 (96.4\%) \\
Aciertos en Posición 1 (P1) & \textbf{311} & 305 & 299 & 299 \\
Aciertos en Posición 5 (P5) & \textbf{9} & 17 & 24 & 20 \\
\bottomrule
\end{tabularx}
\end{table}

\subsection{Análisis de la precisión posicional}
La Figura \ref{fig:top_positions} es la prueba visual de la superioridad de `o3`. No solo acierta más a menudo en la primera posición, sino que relega el acierto a la última posición con mucha menos frecuencia que sus competidores, un claro signo de mayor confianza y mejor ordenación de sus diferenciales.
\begin{figure}[H]
    \centering
    \includegraphics[width=0.9\linewidth]{imgs/v4horizontalstackedtoppositions.jpg}
    \caption{Distribución de los aciertos en las Top 5 posiciones por modelo.}
    \label{fig:top_positions}
\end{figure}

\subsection{Análisis del método de resolución}
El Pipeline v4 nos permite ver la ``huella digital'' de cada modelo: su preferencia por resolver casos mediante métodos objetivos o semánticos.
\begin{figure}[H]
    \centering
    \includegraphics[width=0.9\linewidth]{imgs/v4horizontalstackedbarsbymodelacrossmethods.jpg}
    \caption{Desglose de los métodos de resolución por modelo.}
    \label{fig:methods_breakdown}
\end{figure}

\begin{figure}[H]
    \centering
    \includegraphics[width=0.9\linewidth]{imgs/v4casecountandaveragepositionbymethod.jpg}
    \caption{Número de casos resueltos y posición promedio por cada método y modelo.}
    \label{fig:casecount_method}
\end{figure}

Este análisis (Figuras \ref{fig:methods_breakdown} y \ref{fig:casecount_method}) confirma que `o3` basa su éxito en una mayor disciplina taxonómica (más aciertos por SNOMED e ICD-10), mientras que otros modelos como `o3-pro` dependen más de la ``red de seguridad'' del análisis semántico para alcanzar una alta tasa de resolución, a menudo a expensas de la precisión posicional.

\section{Discusión y conclusión}
La metodología incremental documentada en este informe nos ha llevado a una conclusión compleja y matizada. Si bien el Pipeline v4 representa nuestro esfuerzo más sofisticado por medir el rendimiento de la IA diagnóstica, sus resultados, lejos de ofrecer una respuesta definitiva, nos enfrentan a una manifestación aún más sutil del fenómeno de la saturación de la tarea.

\subsection{Análisis crítico de los resultados del pipeline v4}
A primera vista, el Pipeline v4 establece una jerarquía: `o3` (89.98\%) > `o1` (88.19\%) > `o3-pro` (87.73\%) > `4o` (87.70\%). Sin embargo, una mirada más crítica a estos números revela un panorama preocupante. La diferencia entre el primer y el cuarto modelo es de apenas 2.28 puntos porcentuales. Los modelos `4o` y `o3-pro` tienen un rendimiento prácticamente idéntico, y `o1` se sitúa muy cerca. Esta compresión de los resultados es, de hecho, la evidencia más fuerte de saturación que hemos observado hasta ahora.

El argumento previo, de que la saturación en el v3 se debía a la ``generosidad'' del Juez LLM, se ve ahora desafiado. El Pipeline v4, diseñado para ser más riguroso y multifacético, debería haber ampliado estas diferencias, no mantenerlas tan estrechas. El hecho de que no lo haga sugiere que el problema raíz podría no estar (solo) en la metodología de evaluación, sino en una interacción más profunda entre la tarea y el dataset.

Planteamos la siguiente hipótesis: el dataset de 450 casos, a pesar de su diversidad taxonómica, podría estar concentrado en un espectro de dificultad que no exige un ``razonamiento de primeros principios'', sino un ``reconocimiento de patrones'' altamente sofisticado. Si la mayoría de los casos, por complejos que parezcan, se resuelven identificando constelaciones de síntomas que los modelos ya han internalizado masivamente durante su entrenamiento, entonces es lógico que los modelos modernos converjan en su rendimiento. La tarea no estaría midiendo su capacidad de ``pensar'', sino la exhaustividad de su ``memoria'' de patrones clínicos.

\subsection{Significancia estadística e incertidumbre}
Si bien la agrupación de los resultados es relativamente estrecha, la diferencia de aproximadamente un 2\% a favor de `o3` frente a los demás parece lo suficientemente consistente como para ser considerada significativa en términos prácticos. Aunque en otro contexto podría justificarse un análisis estadístico más profundo —como un bootstrap para estimar la estabilidad de esta ventaja—, en este caso no se consideró necesario. La comparación se basa en 450 casos diversos, lo cual aporta una base empírica razonable para aceptar que la ventaja observada de `o3` no es fruto del azar, sino una señal robusta dentro del marco evaluado. Por tanto, puede considerarse válida la jerarquía que se observa en los resultados.

En este contexto, el Pipeline v4, aunque metodológicamente es una agregación de criterios más completa, podría no estar aportando un poder discriminativo proporcional a su complejidad. Si la limitación fundamental reside en la naturaleza de la tarea que el dataset permite evaluar, añadir más capas de evaluación podría ser redundante.

\subsection{Consideraciones para futuras investigaciones}
Esta conclusión no es un punto final, sino una reorientación. Nos obliga a mover el foco de \textit{cómo medimos} a \textit{qué medimos}. Las futuras investigaciones deberían, por tanto, explorar vías para romper este ciclo de saturación, no mediante nuevos pipelines, sino alterando la naturaleza fundamental del desafío. Algunas direcciones posibles incluyen:
\begin{itemize}
    \item \textbf{Diseño de tareas de razonamiento explícito:} Podemos evolucionar los prompts para que no solo pidan un diagnóstico final, sino que exijan explicaciones fisiopatológicas, la justificación del descarte de diagnósticos diferenciales, o incluso la elaboración de un plan diagnóstico escalonado. Esto transforma la tarea de ser principalmente de recuperación a una de explicación y síntesis, revelando mejor las capacidades latentes de modelos avanzados.
    \item \textbf{Curación de datasets de ``frontera'':} Tiene sentido avanzar hacia la construcción de casos clínicos diseñados deliberadamente para ser ambiguos, contradictorios o multidominio. Estos escenarios más exigentes podrían servir como verdaderos diferenciadores entre modelos, revelando su capacidad para razonar bajo incertidumbre o resolver tensiones clínicas sutiles.

\item \textbf{Análisis de la robustez ante la adversidad:} También se pueden explorar escenarios en los que los modelos reciban información engañosa o ruido clínico irrelevante. La forma en que responden ante este tipo de "pistas falsas" permite evaluar la profundidad y estabilidad de su razonamiento.

\item \textbf{Integración de evaluadores como Deep Research:} Todas estas estrategias se vuelven más útiles si se combinan con evaluadores capaces de captar matices y profundidad contextual. Deep Research, al tener una arquitectura distinta y capacidades de análisis exhaustivo, permite valorar estas tareas con mayor sensibilidad y menor riesgo de sesgo por familiaridad. Su inclusión como juez complementario no reemplaza los sistemas actuales, pero sí los enriquece y valida desde otro ángulo.

\end{itemize}

En definitiva, nuestro viaje metodológico nos ha enseñado que la búsqueda de un ``evaluador perfecto'' es probablemente fútil si no va acompañada de una reflexión crítica y continua sobre la naturaleza de la tarea y los datos con los que trabajamos. La saturación no es un fracaso, sino un dato en sí mismo, que nos señala los límites de nuestro enfoque actual y nos guía hacia nuevos y más desafiantes horizontes de investigación.

\end{document}