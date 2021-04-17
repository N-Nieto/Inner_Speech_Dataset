function [mrks_general,mrks_modalidad,mrks_clase,mrks_xTrial,mrks_descansos,mrks_clase_q]=Set_up_Marcadores

% Marcadores por LSL
mrks_general = [11,12,13,14,15,16,17];
% markers_general = {'Comienza Experimento','Fin Experimento',Comienza Baseline','Fin Baseline'
%                   'Comienzo Bloque','Fin Bloque' ,'Comienzo Etapa','Fin Etapa,'Inicio Pregunta'}
mrks_modalidad = [21, 22,23];
% markers_xTrial = {'Pronunciada', Imaginada','Visualizacion'};
mrks_clase = [31, 32,33,34,35];
% markers_clase = {'Arriba', 'Abajo', 'Derecha', 'Izquierda' , 'Seleccionar'}
mrks_xTrial = [41, 42,40,44,45,46,47];
% markers_xTrial = { Comienza Trial, Comienzo Concentracion, Comienzo de Estimulo ..
%                   Comienzo Intervalo Util, Comienzo concentracion 2, Comienzo descanso, Fin Trial}
mrks_descansos = [51];
% markers_descansos = {'Descanso interbloque' };

mrks_clase_q= [61,62,63,64,65];
% markers_clase_q = {'Arriba', 'Abajo', 'Derecha', 'Izquierda' , 'Seleccionar'}