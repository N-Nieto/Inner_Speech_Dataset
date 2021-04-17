function [N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales]= send_value_pp (mrk,lptport,dir,time_pause,N_dato,Datos_Enviados,Tiempo_parcial,Tiempos_parciales)

Tiempo_parcial=toc(Tiempo_parcial);
Tiempos_parciales(N_dato)=Tiempo_parcial;
Tiempo_parcial=tic;


Datos_Enviados(N_dato)=mrk;
N_dato=N_dato+1;
% lptwrite(lptport, mrk+dir);
pause(time_pause)
% lptwrite(lptport, dir)

