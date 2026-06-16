/*
 * UART Command Processor for LVDT Controller
 */

/*
 * UART Command Processor for LVDT Controller
 */

#include "uart.h"
#include "eeprom.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdarg.h>

/* lvdt_cl.h is already included via uart.h */
/* No need to include it again */

static UART_HandleTypeDef *cmd_huart = NULL;
static LVDT_Controller *cmd_controller = NULL;
static char cmd_buffer[CMD_BUFFER_SIZE];
static uint16_t cmd_index = 0;
static char response_buffer[CMD_RESPONSE_SIZE];

/* Rest of the file remains the same */

/* Simple checksum for validation */
static uint8_t calculate_pid_checksum(float Kp, float Ki, float Kd, uint16_t magic)
{
    uint8_t *kp_bytes = (uint8_t*)&Kp;
    uint8_t *ki_bytes = (uint8_t*)&Ki;
    uint8_t *kd_bytes = (uint8_t*)&Kd;
    uint8_t sum = 0;
    int i;

    for (i = 0; i < 4; i++) {
        sum += kp_bytes[i];
        sum += ki_bytes[i];
        sum += kd_bytes[i];
    }
    sum += (magic >> 8) & 0xFF;
    sum += magic & 0xFF;

    return sum;
}

/* Save PID gains to EEPROM */
uint8_t UART_SavePIDGains(float Kp, float Ki, float Kd)
{
    uint8_t checksum;
    uint16_t magic = PID_MAGIC_NUMBER;

    /* Write Kp */
    if (EEPROM_WriteBuffer(EEPROM_PID_KP_ADDR, (uint8_t*)&Kp, sizeof(float)) != EEPROM_OK)
        return 0;

    /* Write Ki */
    if (EEPROM_WriteBuffer(EEPROM_PID_KI_ADDR, (uint8_t*)&Ki, sizeof(float)) != EEPROM_OK)
        return 0;

    /* Write Kd */
    if (EEPROM_WriteBuffer(EEPROM_PID_KD_ADDR, (uint8_t*)&Kd, sizeof(float)) != EEPROM_OK)
        return 0;

    /* Write magic number */
    if (EEPROM_WriteBuffer(EEPROM_PID_MAGIC, (uint8_t*)&magic, sizeof(uint16_t)) != EEPROM_OK)
        return 0;

    /* Write checksum */
    checksum = calculate_pid_checksum(Kp, Ki, Kd, magic);
    if (EEPROM_WriteByte(EEPROM_PID_CHECK, checksum) != EEPROM_OK)
        return 0;

    return 1;
}

/* Load PID gains from EEPROM */
uint8_t UART_LoadPIDGains(float *Kp, float *Ki, float *Kd)
{
    uint16_t magic;
    uint8_t stored_checksum, calculated_checksum;
    float temp_kp, temp_ki, temp_kd;

    /* Read magic number */
    if (EEPROM_ReadBuffer(EEPROM_PID_MAGIC, (uint8_t*)&magic, sizeof(uint16_t)) != EEPROM_OK)
        return 0;

    if (magic != PID_MAGIC_NUMBER)
        return 0;

    /* Read gains */
    if (EEPROM_ReadBuffer(EEPROM_PID_KP_ADDR, (uint8_t*)&temp_kp, sizeof(float)) != EEPROM_OK)
        return 0;

    if (EEPROM_ReadBuffer(EEPROM_PID_KI_ADDR, (uint8_t*)&temp_ki, sizeof(float)) != EEPROM_OK)
        return 0;

    if (EEPROM_ReadBuffer(EEPROM_PID_KD_ADDR, (uint8_t*)&temp_kd, sizeof(float)) != EEPROM_OK)
        return 0;

    /* Verify checksum */
    calculated_checksum = calculate_pid_checksum(temp_kp, temp_ki, temp_kd, magic);
    if (EEPROM_ReadByte(EEPROM_PID_CHECK, &stored_checksum) != EEPROM_OK)
        return 0;

    if (calculated_checksum != stored_checksum)
        return 0;

    *Kp = temp_kp;
    *Ki = temp_ki;
    *Kd = temp_kd;

    return 1;
}

/* Initialize command processor */
void UART_Commands_Init(UART_HandleTypeDef *huart, LVDT_Controller *controller)
{
    cmd_huart = huart;
    cmd_controller = controller;
    cmd_index = 0;
    memset(cmd_buffer, 0, CMD_BUFFER_SIZE);

    /* Print welcome message */
    char welcome[] = "\r\n=== LVDT Controller v1.0 ===\r\n";
    HAL_UART_Transmit(cmd_huart, (uint8_t*)welcome, strlen(welcome), 100);

    /* Try to load saved PID gains */
    float saved_kp, saved_ki, saved_kd;
    if (UART_LoadPIDGains(&saved_kp, &saved_ki, &saved_kd)) {
        LVDT_SetPIDTunings(cmd_controller, saved_kp, saved_ki, saved_kd);
        char msg[100];
        snprintf(msg, sizeof(msg), "[EEPROM] Loaded: Kp=%.2f, Ki=%.2f, Kd=%.3f\r\n",
                 saved_kp, saved_ki, saved_kd);
        HAL_UART_Transmit(cmd_huart, (uint8_t*)msg, strlen(msg), 100);
    } else {
        char msg[] = "[EEPROM] No saved config, using defaults\r\n";
        HAL_UART_Transmit(cmd_huart, (uint8_t*)msg, strlen(msg), 100);
    }

    /* Print help */
    char help[] = "\r\nCommands:\r\n"
                  "  kp=<val>     - Set Kp (0-5000)\r\n"
                  "  ki=<val>     - Set Ki (0-500)\r\n"
                  "  kd=<val>     - Set Kd (0-100)\r\n"
                  "  pid=x,y,z    - Set all gains\r\n"
                  "  status       - Show status\r\n"
                  "  save         - Save to EEPROM\r\n"
                  "  load         - Load from EEPROM\r\n"
                  "  reset        - Reset to defaults\r\n"
                  "  help         - Show this\r\n"
                  "\r\n> ";
    HAL_UART_Transmit(cmd_huart, (uint8_t*)help, strlen(help), 100);
}

/* Send response via UART */
void UART_SendResponse(const char *format, ...)
{
    if (cmd_huart == NULL) return;

    va_list args;
    int len;

    va_start(args, format);
    len = vsnprintf(response_buffer, CMD_RESPONSE_SIZE - 1, format, args);
    va_end(args);

    if (len > 0 && len < CMD_RESPONSE_SIZE) {
        HAL_UART_Transmit(cmd_huart, (uint8_t*)response_buffer, len, 100);
    }
}

/* Process a complete command */
static void process_command(void)
{
    char *cmd = cmd_buffer;
    float kp_val, ki_val, kd_val;
    char *token;

    /* Remove newline characters */
    char *newline = strchr(cmd, '\r');
    if (newline) *newline = '\0';
    newline = strchr(cmd, '\n');
    if (newline) *newline = '\0';

    /* Skip if empty */
    if (strlen(cmd) == 0) {
        UART_SendResponse("> ");
        return;
    }

    /* kp command */
    if (strncmp(cmd, "kp=", 3) == 0) {
        kp_val = atof(cmd + 3);
        if (kp_val >= 0 && kp_val <= 5000) {
            LVDT_SetPIDTunings(cmd_controller, kp_val,
                              cmd_controller->pid.Ki,
                              cmd_controller->pid.Kd);
            UART_SendResponse("Kp = %.2f\r\n> ", kp_val);
        } else {
            UART_SendResponse("Error: Kp must be 0-5000\r\n> ");
        }
    }
    /* ki command */
    else if (strncmp(cmd, "ki=", 3) == 0) {
        ki_val = atof(cmd + 3);
        if (ki_val >= 0 && ki_val <= 500) {
            LVDT_SetPIDTunings(cmd_controller,
                              cmd_controller->pid.Kp,
                              ki_val,
                              cmd_controller->pid.Kd);
            UART_SendResponse("Ki = %.2f\r\n> ", ki_val);
        } else {
            UART_SendResponse("Error: Ki must be 0-500\r\n> ");
        }
    }
    /* kd command */
    else if (strncmp(cmd, "kd=", 3) == 0) {
        kd_val = atof(cmd + 3);
        if (kd_val >= 0 && kd_val <= 100) {
            LVDT_SetPIDTunings(cmd_controller,
                              cmd_controller->pid.Kp,
                              cmd_controller->pid.Ki,
                              kd_val);
            UART_SendResponse("Kd = %.3f\r\n> ", kd_val);
        } else {
            UART_SendResponse("Error: Kd must be 0-100\r\n> ");
        }
    }
    /* pid command */
    else if (strncmp(cmd, "pid=", 4) == 0) {
        token = strtok(cmd + 4, ",");
        if (token) kp_val = atof(token);
        else goto pid_error;

        token = strtok(NULL, ",");
        if (token) ki_val = atof(token);
        else goto pid_error;

        token = strtok(NULL, ",");
        if (token) kd_val = atof(token);
        else goto pid_error;

        if (kp_val >= 0 && kp_val <= 5000 &&
            ki_val >= 0 && ki_val <= 500 &&
            kd_val >= 0 && kd_val <= 100) {
            LVDT_SetPIDTunings(cmd_controller, kp_val, ki_val, kd_val);
            UART_SendResponse("PID: Kp=%.2f, Ki=%.2f, Kd=%.3f\r\n> ",
                            kp_val, ki_val, kd_val);
        } else {
            UART_SendResponse("Error: Invalid range (Kp:0-5000, Ki:0-500, Kd:0-100)\r\n> ");
        }
        goto pid_done;

        pid_error:
        UART_SendResponse("Usage: pid=<kp>,<ki>,<kd>\r\n> ");
        pid_done:;
    }
    /* status command */
    else if (strcmp(cmd, "status") == 0 || strcmp(cmd, "stat") == 0) {
        UART_SendResponse("\r\n--- PID Gains ---\r\n");
        UART_SendResponse("Kp: %.2f\r\n", cmd_controller->pid.Kp);
        UART_SendResponse("Ki: %.2f\r\n", cmd_controller->pid.Ki);
        UART_SendResponse("Kd: %.3f\r\n", cmd_controller->pid.Kd);
        UART_SendResponse("\r\n--- Live Data ---\r\n");
        UART_SendResponse("Setpoint: %.3f V\r\n", cmd_controller->setpoint_voltage);
        UART_SendResponse("Feedback: %.3f V\r\n", cmd_controller->feedback_voltage);
        UART_SendResponse("Error: %.3f V\r\n", cmd_controller->error_voltage);
        UART_SendResponse("Target: %.3f V\r\n", cmd_controller->target_feedback);
        UART_SendResponse("Output: %.1f\r\n", cmd_controller->output);
        UART_SendResponse("\r\n> ");
    }
    /* save command */
    else if (strcmp(cmd, "save") == 0) {
        if (UART_SavePIDGains(cmd_controller->pid.Kp,
                              cmd_controller->pid.Ki,
                              cmd_controller->pid.Kd)) {
            UART_SendResponse("Gains saved to EEPROM\r\n> ");
        } else {
            UART_SendResponse("EEPROM write failed!\r\n> ");
        }
    }
    /* load command */
    else if (strcmp(cmd, "load") == 0) {
        float saved_kp, saved_ki, saved_kd;
        if (UART_LoadPIDGains(&saved_kp, &saved_ki, &saved_kd)) {
            LVDT_SetPIDTunings(cmd_controller, saved_kp, saved_ki, saved_kd);
            UART_SendResponse("Loaded: Kp=%.2f, Ki=%.2f, Kd=%.3f\r\n> ",
                            saved_kp, saved_ki, saved_kd);
        } else {
            UART_SendResponse("No valid config in EEPROM!\r\n> ");
        }
    }
    /* reset command */
    else if (strcmp(cmd, "reset") == 0) {
        LVDT_SetPIDTunings(cmd_controller, 1000.0, 40.0, 0.10);
        UART_SendResponse("Reset to defaults: Kp=1000, Ki=40, Kd=0.1\r\n> ");
    }
    /* help command */
    else if (strcmp(cmd, "help") == 0 || strcmp(cmd, "?") == 0) {
        UART_SendResponse("\r\nCommands:\r\n");
        UART_SendResponse("  kp=<val>     - Set Kp (0-5000)\r\n");
        UART_SendResponse("  ki=<val>     - Set Ki (0-500)\r\n");
        UART_SendResponse("  kd=<val>     - Set Kd (0-100)\r\n");
        UART_SendResponse("  pid=x,y,z    - Set all gains\r\n");
        UART_SendResponse("  status       - Show current status\r\n");
        UART_SendResponse("  save         - Save gains to EEPROM\r\n");
        UART_SendResponse("  load         - Load gains from EEPROM\r\n");
        UART_SendResponse("  reset        - Reset to defaults\r\n");
        UART_SendResponse("  help         - Show this help\r\n");
        UART_SendResponse("\r\nExample: pid=1200,45,0.12\r\n> ");
    }
    /* unknown command */
    else {
        UART_SendResponse("Unknown: '%s' (type 'help')\r\n> ", cmd);
    }
}

/* Process received character - called from interrupt */
void UART_ProcessChar(uint8_t c)
{
    /* Handle backspace/delete */
    if (c == 0x08 || c == 0x7F) {
        if (cmd_index > 0) {
            cmd_index--;
            cmd_buffer[cmd_index] = '\0';
            /* Send backspace sequence to erase character */
            uint8_t bs[] = {'\b', ' ', '\b'};
            HAL_UART_Transmit(cmd_huart, bs, 3, 10);
        }
        return;
    }

    /* Handle carriage return or line feed (Enter key) */
    if (c == '\r' || c == '\n') {
        /* Only process on CR, ignore LF if it follows CR */
        if (c == '\r') {
            /* Send newline */
            uint8_t newline[] = {'\r', '\n'};
            HAL_UART_Transmit(cmd_huart, newline, 2, 10);

            /* Process the command */
            if (cmd_index > 0) {
                process_command();
                cmd_index = 0;
                memset(cmd_buffer, 0, CMD_BUFFER_SIZE);
            }
        }
        return;
    }

    /* Store character if buffer not full and printable */
    if (cmd_index < CMD_BUFFER_SIZE - 1 && c >= 0x20 && c <= 0x7E) {
        cmd_buffer[cmd_index++] = c;
        cmd_buffer[cmd_index] = '\0';
        /* Echo character back */
        HAL_UART_Transmit(cmd_huart, &c, 1, 10);
    }
}
