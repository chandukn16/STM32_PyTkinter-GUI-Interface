#ifndef UART_H
#define UART_H

#ifdef __cplusplus
extern "C" {
#endif

#include "stm32f4xx_hal.h"
#include <stdint.h>
#include <stdarg.h>

/* Include the actual definition - no forward declaration needed */
#include "lvdt_cl.h"

/* Command buffer size */
#define CMD_BUFFER_SIZE    64
#define CMD_RESPONSE_SIZE  128

/* PID gain storage addresses in EEPROM (using block 1, addresses 0x100-0x10F) */
#define EEPROM_PID_KP_ADDR  0x0100  /* 4 bytes - float */
#define EEPROM_PID_KI_ADDR  0x0104  /* 4 bytes - float */
#define EEPROM_PID_KD_ADDR  0x0108  /* 4 bytes - float */
#define EEPROM_PID_MAGIC    0x010C  /* 2 bytes - validation magic (0x5A5A) */
#define EEPROM_PID_CHECK    0x010E  /* 1 byte  - checksum */

#define PID_MAGIC_NUMBER    0x5A5A

/* Function prototypes */
void UART_Commands_Init(UART_HandleTypeDef *huart, LVDT_Controller *controller);
void UART_ProcessChar(uint8_t c);
void UART_SendResponse(const char *format, ...);
uint8_t UART_SavePIDGains(float Kp, float Ki, float Kd);
uint8_t UART_LoadPIDGains(float *Kp, float *Ki, float *Kd);

#ifdef __cplusplus
}
#endif

#endif /* UART_H */
