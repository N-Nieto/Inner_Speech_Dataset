function [mrk]= Realizar_Pregunta(mrks_clase_q)
exit_q=false;
% Codigo de cada letra
upKey = KbName('UpArrow');
downKey = KbName('DownArrow');
leftKey = KbName('LeftArrow');
rightKey = KbName('RightArrow');
while exit_q == false
                % Interrupción por teclado
                [~,~, keyCode] = KbCheck;
                if keyCode(upKey)
                    mrk = mrks_clase_q(1);
                    exit_q = true;
                elseif keyCode(downKey)
                    mrk = mrks_clase_q(2);
                    exit_q = true;
                elseif keyCode(rightKey)
                    mrk = mrks_clase_q(3);
                    exit_q = true;
                elseif keyCode(leftKey)
                    mrk = mrks_clase_q(4);
                    exit_q = true;
                end
end
end