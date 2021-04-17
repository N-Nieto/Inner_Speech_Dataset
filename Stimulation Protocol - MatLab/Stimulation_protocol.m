%% ------------------ Stimulation protocol --------------------------------
% Developed by Nicolás Nieto and Victoria Peterson.
% Corresponds to the Inner speech dataset
%% ----------------------------SET UPs-------------------------------------
%--------------------------------------------------------------------------
%% General Set Up 
% Clean
close all; clear; clc;
Screen('Preference', 'SkipSyncTests', 1)
% Add path with where the auxiliary functions are stored
addpath(genpath('./'));
%% --------------------------- Subject Info -------------------------------
%--------------------------------------------------------------------------
% Create a struct where all the information will be stored
Experiment=[];
Experiment.S.ID= '00';
Experiment.S.Age= '29';
Experiment.S.Dominance='Derecha';
Experiment.S.Gender='F';
Experiment.S.Block=3;

%% --------------------------- Protocol set up ----------------------------
%--------------------------------------------------------------------------
%% Protocolo Set Up

Paradigms = {'Pronounced Speech', 'Inner Speech','Visualized Condition'};

Classes ={ 'Up', 'Down', 'Right', 'Left'};

% Number of classes
N_classes=size(Classes,2);

% Amount of trials for each class in every run
TriasxRuns=10;

% Paradigms Order 
% 1 = Pronounced Speech
% 2 =  Inner speech
% 3 = Visualized condition
Paradigms_order=[1,2,2,3,3];

% Store in struct
Experiment.Protocol.Paradigms = Paradigms;
Experiment.Protocol.Classes = Classes;
Experiment.Protocol.TriasxRuns = TriasxRuns;
Experiment.Protocol.Paradigms_order= Paradigms_order;

%% Protocol Timing set up

% Tiempo en el que aparece la fix coss hasta que aparece el estimulo
T_Concentracion1=0.5;
% Tiempo entre que aparece el estimulo y comienzo a grabar (Evito P300)
T_Estimulo=2;
% Tiempo útil de grabacion
T_Imaginacion=2.5;
% Desaparece el estimulo pero permanece la fix coss (sin parpadeo)
% Interlvalo útil para caracterizar el baseline de EEG
T_Concentracion2=1;
% Tiempo de descanso InterTrial variable (Se permite parpadeo)
T_Descanso_min=1.5;
T_Descanso_max=2;
% Tiempo de baseline
T_baseline= 5;
% Descansos Inter bloque
T_Descanso_Interbloque=4;

Tiempos_parciales=[];
% Guardo en stc
Experiment.Tiempos.T_Concentracion1= T_Concentracion1;
Experiment.Tiempos.T_Estimulo= T_Estimulo;
Experiment.Tiempos.T_Imaginacion= T_Imaginacion;
Experiment.Tiempos.T_Concentracion2= T_Concentracion2;
Experiment.Tiempos.T_Descanso_min= T_Descanso_min;
Experiment.Tiempos.T_Descanso_max= T_Descanso_max;
Experiment.Tiempos.T_baseline= T_baseline;
Experiment.Tiempos.T_Descanso_Interbloque= T_Descanso_Interbloque;

%% ----------------- Matrices de Estimulacion y modalidad -----------------
% Vector de estimuo
Est=1:N_classes;
Est=repmat(Est,[1,TriasxRuns]);
% Modalidad por bloque
N_trials_bloque=size(Est,2);
N_bloques=size(Paradigms_order,2);

%%  Psicotoolbox Set Up
% Configuraciones de PsicoToolbox
N_defaultsetup=2;
% Tamano del texto
Text_size=40;
% Fuente : 'Courier' , 'Times', 'Arial'
Text_font='Times';

Experiment.Psicotoolbox.N_defaultsetup= N_defaultsetup;
Experiment.Psicotoolbox.Text_size= Text_size;
Experiment.Psicotoolbox.Text_font= Text_font;
%% Parallel Set Up 0 to 255
[mrks_general,mrks_modalidad,mrks_clase,mrks_xTrial,mrks_descansos,mrks_clase_q]=Set_up_Marcadores;

Experiment.Marcadores.mrks_general= mrks_general;
Experiment.Marcadores.mrks_modalidad= mrks_modalidad;
Experiment.Marcadores.mrks_clase= mrks_clase;
Experiment.Marcadores.mrks_xTrial= mrks_xTrial;
Experiment.Marcadores.mrks_descansos= mrks_descansos;
Experiment.Marcadores.mrks_clase_q= mrks_clase_q;
%% Imagenes del protocolo Set up
Color_fondo=0 ;
% Color del los estimulos
Tamano_punto=20;
color_punto=0.95;
color_punto_2=[0 0 1] ;
color_letra=0.95;
y_letra=500;
% estimulo
Ancho_triangulo = 25;
Ancho  = 150;           % width of arrow head
Alto=200;
Experiment.Estimulos.Color_fondo= Color_fondo;
Experiment.Estimulos.Tamano_punto= Tamano_punto;
Experiment.Estimulos.color_punto_2= color_punto_2;
Experiment.Estimulos.color_letra= color_letra;
Experiment.Estimulos.y_letra= y_letra;
Experiment.Estimulos.Ancho_triangulo= Ancho_triangulo;
Experiment.Estimulos.Ancho= Ancho;
Experiment.Estimulos.Alto= Alto;

%% ----------------------- CONFIGURACION Puerto Paralelo-------------------
%--------------------------------------------------------------------------
portDir = 'C100';
lptport = hex2dec(portDir);
dir = hex2dec('0'); % Código base. Del que parte y al que vuelve dsp de cada marca
time_pause=0.1;

Experiment.Comunicacion.portDir= portDir;
Experiment.Comunicacion.lptport= lptport;
Experiment.Comunicacion.dir= dir;
Experiment.Comunicacion.time_pause= time_pause;

%% SCREEN SET UP
PsychDefaultSetup(N_defaultsetup);
% Get the screen numbers
screens = Screen('Screens');
% Numero de pantallas maximas
screenNumber = max(screens);
% Define black % white
% Open an on screen window and color it black
[window, windowRect] = PsychImaging('OpenWindow', screenNumber, Color_fondo);
% Set the blend funciton for the screen
Screen('BlendFunction', window, 'GL_SRC_ALPHA', 'GL_ONE_MINUS_SRC_ALPHA');
% Flip to clear
Screen('Flip', window);
% Pixeles centrales
[xCenter, yCenter] = RectCenter(windowRect);
% Tamaño del texto
Screen('TextSize', window, Text_size);
Screen('TextFont', window, Text_font);

Experiment.Psicotoolbox.xCenter= xCenter;
Experiment.Psicotoolbox.yCenter= yCenter;
Experiment.Psicotoolbox.screenNumber= screenNumber;
%% Pregunta de concentración
% Cantidad minima de trials para realizar una regunta
min_q=3;
% Cantidad maxima de trials para realizar una regunta
max_q=4;
max_q= min(max_q,N_trials_bloque);
min_q=min(min_q,max_q);

% Primer numero de trials para realizar la primer pregunta, este numero se
% va actualizando despues de cada pregunta de forma aleatoria
N_q=min_q+round(rand(1,1)*(max_q-min_q));

cont_cor=0;
cont_mal=0;

Experiment.Pregunta.min_q= min_q;
Experiment.Pregunta.max_q= max_q;
%% ---------------------Parametros de Graficas-----------------------------
Puntos=Set_up_Estimulos(xCenter,yCenter,Alto,Ancho);

Experiment.Estimulos.Puntos= Puntos;
%% ------------------------------------------------------------------------
%% ---------------------EJECUCION DEL PROTOCOLO----------------------------
%% ------------------------------------------------------------------------
% Inicialización
N_dato=1;
Datos_Enviados=[];
%% ---------------------Grabacion de Baseline -----------------------------
%--------------------------------------------------------------------------
Tiempo_total=tic;
Tiempo_parcial=tic;
% MARCADOR Comienza el experimento
DrawFormattedText(window, 'Vamos a comenzar con el experimento', 'center', 'center', color_letra);
Screen('Flip', window);
% MARCADOR Comienza el experimento
mrk = mrks_general(1);
[N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales]= send_value_pp (mrk,lptport,dir,time_pause,N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales);
WaitSecs(10);

DrawFormattedText(window, strcat('Relajado durante:\n\n ',num2str(T_baseline),' segundos'), 'center', 'center', color_letra);
Screen('Flip', window);
% MARCADOR comienza el Baseline
mrk = mrks_general(3);
[N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales]= send_value_pp (mrk,lptport,dir,time_pause,N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales);
WaitSecs(T_baseline);
% MARCADOR Termina el Baseline
mrk = mrks_general(4);
[N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales]= send_value_pp (mrk,lptport,dir,time_pause,N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales);
%% ---------------------PROTOCOLO de estimulacion--------------------------

DrawFormattedText(window, '¿Listo para empezar?', 'center', 'center', color_letra);
Screen('Flip', window);
WaitSecs(2);
DrawFormattedText(window, 'Comenzamos!', 'center', 'center', color_letra);
Screen('Flip', window);
WaitSecs(2);


for bloque=1:N_bloques
    % MARCADOR Comienzo de bloque
    mrk = mrks_general(5);
    [N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales]= send_value_pp (mrk,lptport,dir,time_pause,N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales);
    % Cambio el orden de los estimulos en cada bloque
    Est=Shuffle(Est);
    %Selecciono una modalidad aleatoriamente
    Mod_n = Paradigms_order(bloque);
    Mod_str=Paradigms{Mod_n};
    % MARCADOR modalidad Pronunciada
    mrk = mrks_modalidad(Mod_n);
    [N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales]= send_value_pp (mrk,lptport,dir,time_pause,N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales);
    
    DrawFormattedText(window, strcat('Modalidad: ',Mod_str), 'center', 'center', color_letra);
    Screen('Flip', window);
    WaitSecs(3);
    count_preg=0;
    for n_trial=1:N_trials_bloque
        count_preg=count_preg+1;
        %% Comienzo de trial
        mrk = mrks_xTrial(1);
        [N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales]= send_value_pp (mrk,lptport,dir,time_pause,N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales);
        
        %% Periodo de concentracion
        % MOSTRAR Punto
        Screen('DrawDots', window, [xCenter yCenter], Tamano_punto,color_punto , [], 2);
        Screen('Flip', window);
        % MARCADOR Concentracion
        mrk = mrks_xTrial(2);
        [N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales]= send_value_pp (mrk,lptport,dir,time_pause,N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales);
        % Tiempo de concentracion
        WaitSecs(T_Concentracion1);
        
        %% Periodo de Estimulacion
        % MOSTRAR Punto
        Screen('DrawDots', window, [xCenter yCenter], Tamano_punto, color_punto, [], 2);
        % Seleccion de estimulo
        n_sel= Est(n_trial);
        triangulo= Puntos{n_sel};
        Screen('FramePoly', window,[200,200,200], triangulo,Ancho_triangulo);
        Screen('Flip', window);
        % MARCADOR Estimulo
        mrk_c = mrks_clase(n_sel);
        [N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales]= send_value_pp (mrk_c,lptport,dir,time_pause,N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales);
        
        % Tiempo para eliminar el P300
        WaitSecs(T_Estimulo);
        
        %% Periodo útil de adquisicion
        % MOSTRAR Punto
        Screen('DrawDots', window, [xCenter yCenter], Tamano_punto, color_punto, [], 2);
        Screen('Flip', window);
        % MARCADOR Estimulacion
        mrk = mrks_xTrial(4);
        [N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales]= send_value_pp(mrk,lptport,dir,time_pause,N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales);
        % Tiempo útil de adquisicion
        WaitSecs(T_Imaginacion);
        
        %% Periodo de adquisición sin estímulo (para eliminar blinks )
        % MOSTRAR Punto
        Screen('DrawDots', window, [xCenter yCenter], Tamano_punto, color_punto_2, [], 2);
        Screen('Flip', window);
        % MARCADOR Concentracion 2
        mrk = mrks_xTrial(5);
        [N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales]= send_value_pp (mrk,lptport,dir,time_pause,N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales);
        % Tiempo para eliminar blinks
        WaitSecs(T_Concentracion2);
        
        %% Periodo de descanso
        % Pantalla en negro
        Screen('Flip', window);
        % Tiempo de descanso variable
        delta_des= (T_Descanso_max-T_Descanso_min)*rand(1,1);
        % MARCADOR Periodo de Descanso en trial
        mrk = mrks_xTrial(6);
        [N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales]= send_value_pp (mrk,lptport,dir,time_pause,N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales);
        % Si es el ultimo trial no hay descanso
        if n_trial<N_trials_bloque
            WaitSecs(T_Descanso_min+delta_des);
        end
        
        %% Fin del trial
        mrk = mrks_xTrial(7);
        [N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales]= send_value_pp (mrk,lptport,dir,time_pause,N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales);
        
        %% Pregunta de concentracion
        if (count_preg>=N_q && ((strcmp(Mod_str,'Imaginada') || (strcmp(Mod_str,'Visualizado')))))
            % Comienzo Pregunta
            mrk = mrks_general(7);
            [N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales]= send_value_pp (mrk,lptport,dir,time_pause,N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales);
            
            % MARCADOR Fin Bloque
            DrawFormattedText(window, 'Cual fue la última instrucción? \n\n Presione la flecha de la misma', 'center', 'center', color_letra);
            Screen('Flip', window);
            % Nueva cantidad de trials para realizar una nueva pregunta
            N_q= min_q+round(rand(1,1)*(max_q-min_q));
            count_preg=0;
            [mrk_q]= Realizar_Pregunta(mrks_clase_q);
            [N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales]= send_value_pp (mrk_q,lptport,dir,time_pause,N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales);
            
            if mrk_c==mrk_q-30
                DrawFormattedText(window, 'Muy bien!', 'center', 'center', color_letra);
                Screen('Flip', window);
                cont_cor=cont_cor+1;
            else
                DrawFormattedText(window, 'Ojo! Incorrecto!', 'center', 'center', color_letra);
                Screen('Flip', window);
                cont_mal=cont_mal+1;
            end
            WaitSecs(T_Descanso_min);
            DrawFormattedText(window, 'Continuamos!', 'center', 'center', color_letra);
            Screen('Flip', window);
            WaitSecs(T_Descanso_min);
            Screen('Flip', window);
            WaitSecs(T_Descanso_min);
        end
        
        
    end
    
    % MARCADOR Fin Bloque
    mrk = mrks_general(6);
    [N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales]= send_value_pp (mrk,lptport,dir,time_pause,N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales);
    if bloque<N_bloques
        DrawFormattedText(window, 'Final del Bloque', 'center', 'center', color_letra);
        Screen('Flip', window);
        WaitSecs(3);
        % MARCADOR Descanso Inter Bloque
        mrk = mrks_descansos(1);
        [N_dato,Datos_Enviados,Tiempo_parcial,~]= send_value_pp (mrk,lptport,dir,time_pause,N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales);
        for t=T_Descanso_Interbloque:-1:1
            if t==1
                DrawFormattedText(window, strcat('Descanso Breve!\n\n Queda: ',num2str(t), ' segundo y comenzamos'), 'center', 'center', color_letra);
                Screen('Flip', window);
            else
                DrawFormattedText(window, strcat('Descanso Breve!\n\n Quedan: ',num2str(t), ' segundos y comenzamos'), 'center', 'center', color_letra);
                Screen('Flip', window);
            end
            WaitSecs(1);
        end
    end
    
end
WaitSecs(1);
% MARCADOR Finaliza el experimento
mrk = mrks_general(2);
[N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales]= send_value_pp (mrk,lptport,dir,time_pause,N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales);

DrawFormattedText(window, 'Final del Experimento!', 'center', 'center', color_letra);
Screen('Flip', window);
WaitSecs(4);

DrawFormattedText(window, 'Gracias por participar!', 'center', 'center', color_letra);
Screen('Flip', window);
WaitSecs(5);
Tiempo_total=toc(Tiempo_total);

Experiment.Datos.N_dato=N_dato;
Experiment.Datos.Datos_Enviados=Datos_Enviados;
Experiment.Datos.Tiempos_parciales=Tiempos_parciales;
Experiment.Tiempos.Tiempo_total=Tiempo_total;
Experiment.Pregunta.cont_cor= cont_cor;
Experiment.Pregunta.cont_mal= cont_mal;
%% Guardado de Modelo
% Chequeo que no exista el modelo a guardar
if isfile(strcat('Experimento/Sujeto_',Experiment.Sujeto.Nr,'_Etapa_',num2str(Experiment.Sujeto.Etapa),'.mat'))
    %chequeo que no exista un archivo bis
    if isfile(strcat('Experimento/Sujeto_',Experiment.Sujeto.Nr,'_Etapa_',num2str(Experiment.Sujeto.Etapa,'_bis'),'.mat'))
        save(strcat('Experimento/Sujeto_',Experiment.Sujeto.Nr,'_Etapa_',num2str(Experiment.Sujeto.Etapa),'_bis2','.mat'), 'Experimento','-mat');
    else
        save(strcat('Experimento/Sujeto_',Experiment.Sujeto.Nr,'_Etapa_',num2str(Experiment.Sujeto.Etapa),'_bis','.mat'), 'Experimento','-mat');
    end
else
    save(strcat('Experimento/Sujeto_',Experiment.Sujeto.Nr,'_Etapa_',num2str(Experiment.Sujeto.Etapa),'.mat'), 'Experimento','-mat');
end

%% Final
sca
clc
