function [Puntos]=Set_up_Estimulos(xCenter,yCenter,Alto,Ancho)
% create a triangle
head   = [ xCenter, yCenter-Alto/3 ]; % coordinates of head
points_ab = [   head-[Ancho,0]         % left corner
                head+[Ancho,0]         % right corner
                head+[0,Alto] ];      % vertex

head   = [ xCenter, yCenter+Alto/3 ]; % coordinates of head
points_ar = [   head-[Ancho,0]         % left corner
                head+[Ancho,0]         % right corner
                head-[0,Alto] ];      % vertex

head   = [ xCenter-Alto/3, yCenter ]; % coordinates of head
points_dr = [   head-[0,Ancho]         % left corner
                head+[0,Ancho]         % right corner
                head+[Alto,0] ];      % vertex

head   = [ xCenter+Alto/3, yCenter ]; % coordinates of head
points_iz = [   head-[0,Ancho]         % left corner
                head+[0,Ancho]         % right corner
                head-[Alto,0] ];      % vertex

Puntos={points_ar,points_ab,points_dr,points_iz};