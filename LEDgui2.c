/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <string.h>
#include <stdio.h>
#include <ctype.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define RX_BUF_SIZE      64      /* Max command length incl. null terminator */
#define TOGGLE_PERIOD_MS 500     /* LED blink period in toggle mode           */
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
UART_HandleTypeDef huart2;

/* USER CODE BEGIN PV */
/* --- UART RX ring buffer ------------------------------------------------- */
static uint8_t  rxChar;                  /* Single-byte DMA/IT reception     */
static char     rxBuf[RX_BUF_SIZE];     /* Accumulation buffer               */
static uint8_t  rxIdx     = 0;          /* Write index into rxBuf            */
static uint8_t  cmdReady  = 0;          /* Flag: full command waiting        */

/* --- LED state machine --------------------------------------------------- */
typedef enum {
    LED_MODE_OFF    = 0,
    LED_MODE_ON     = 1,
    LED_MODE_TOGGLE = 2
} LED_Mode_t;

static LED_Mode_t ledMode        = LED_MODE_OFF;
static uint32_t   lastToggleTick = 0;    /* For non-blocking 500 ms toggle   */

/* --- Button debounce ----------------------------------------------------- */
static GPIO_PinState lastButtonState = GPIO_PIN_SET;   /* Released (pull-up) */
static uint32_t      lastDebounceTick = 0;
#define DEBOUNCE_MS  50
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_USART2_UART_Init(void);
/* USER CODE BEGIN PFP */
static void UART_SendString(const char *str);
static void ProcessCommand(char *cmd);
static void TrimString(char *str);
static void ToUpperCase(char *str);
static void CheckButton(void);
static void HandleLED(void);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_USART2_UART_Init();
  /* USER CODE BEGIN 2 */
  /* Welcome banner */
  UART_SendString("\r\n========================================\r\n");
  UART_SendString("  STM32 LED Command Processor\r\n");
  UART_SendString("  Commands: ON | OFF | TOGGLE\r\n");
  UART_SendString("  Press Enter to execute a command\r\n");
  UART_SendString("========================================\r\n> ");

  /* Kick off first byte reception in interrupt mode */
  HAL_UART_Receive_IT(&huart2, &rxChar, 1);
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
      /* 1. Process a complete command if Enter was received */
       if (cmdReady)
       {
           cmdReady = 0;
           ProcessCommand(rxBuf);
           memset(rxBuf, 0, sizeof(rxBuf));
           rxIdx = 0;
           UART_SendString("\r\n> ");
       }

       /* 2. Run LED state machine (non-blocking) */
       HandleLED();

       /* 3. Poll button with debounce and report state changes */
       CheckButton();
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief USART2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART2_UART_Init(void)
{

  /* USER CODE BEGIN USART2_Init 0 */

  /* USER CODE END USART2_Init 0 */

  /* USER CODE BEGIN USART2_Init 1 */

  /* USER CODE END USART2_Init 1 */
  huart2.Instance = USART2;
  huart2.Init.BaudRate = 115200;
  huart2.Init.WordLength = UART_WORDLENGTH_8B;
  huart2.Init.StopBits = UART_STOPBITS_1;
  huart2.Init.Parity = UART_PARITY_NONE;
  huart2.Init.Mode = UART_MODE_TX_RX;
  huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart2.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart2) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART2_Init 2 */

  /* USER CODE END USART2_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin : Button_Pin */
  GPIO_InitStruct.Pin = Button_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(Button_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pin : LED_Pin */
  GPIO_InitStruct.Pin = LED_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(LED_GPIO_Port, &GPIO_InitStruct);

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */
/* ═══════════════════════════════════════════════════════════════════════════
 *  UART RX Complete Callback
 *  Called by HAL every time one byte arrives (interrupt mode).
 *  Echoes the character back so the user sees what they type.
 * ═══════════════════════════════════════════════════════════════════════════ */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance != USART2) return;

    uint8_t c = rxChar;

    if (c == '\r' || c == '\n')
    {
        /* Enter pressed → mark command ready, echo newline */
        if (rxIdx > 0)
        {
            rxBuf[rxIdx] = '\0';
            cmdReady = 1;
        }
        /* If rxIdx == 0, ignore empty Enter presses silently */
    }
    else if (c == '\b' || c == 127)
    {
        /* Backspace: delete last character if any */
        if (rxIdx > 0)
        {
            rxIdx--;
            rxBuf[rxIdx] = '\0';
            /* Erase character on terminal: BS + space + BS */
            UART_SendString("\b \b");
        }
    }
    else if (rxIdx < (RX_BUF_SIZE - 1))
    {
        /* Normal printable character: store and echo */
        rxBuf[rxIdx++] = (char)c;
        HAL_UART_Transmit(&huart2, &rxChar, 1, HAL_MAX_DELAY);  /* Echo */
    }
    /* else: buffer full, silently discard */

    /* Re-arm reception for next byte */
    HAL_UART_Receive_IT(&huart2, &rxChar, 1);
}

/* ═══════════════════════════════════════════════════════════════════════════
 *  ProcessCommand  –  Parse and execute a received command string
 * ═══════════════════════════════════════════════════════════════════════════ */
static void ProcessCommand(char *cmd)
{
    TrimString(cmd);      /* Remove leading/trailing whitespace */
    ToUpperCase(cmd);     /* Make comparison case-insensitive   */

    if (strlen(cmd) == 0) return;   /* Ignore blank lines */

    UART_SendString("\r\n");        /* New line before response */

    if (strcmp(cmd, "ON") == 0)
    {
        ledMode = LED_MODE_ON;
        HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, GPIO_PIN_SET);
        UART_SendString("[LED] LED ON\r\n");
    }
    else if (strcmp(cmd, "OFF") == 0)
    {
        ledMode = LED_MODE_OFF;
        HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, GPIO_PIN_RESET);
        UART_SendString("[LED] LED OFF\r\n");
    }
    else if (strcmp(cmd, "TOGLE") == 0)
    {
        ledMode = LED_MODE_TOGGLE;
        lastToggleTick = HAL_GetTick();  /* Reset timer from now */
        UART_SendString("[LED] LED TOGGLING (500ms)\r\n");
    }
    else
    {
        UART_SendString("[ERR] UNKNOWN COMMAND: ");
        UART_SendString(cmd);
        UART_SendString("\r\n      Valid commands: ON | OFF | TOGGLE\r\n");
    }
}

/* ═══════════════════════════════════════════════════════════════════════════
 *  HandleLED  –  Non-blocking LED state machine (call in main loop)
 * ═══════════════════════════════════════════════════════════════════════════ */
static void HandleLED(void)
{
    if (ledMode != LED_MODE_TOGGLE) return;

    uint32_t now = HAL_GetTick();
    if ((now - lastToggleTick) >= TOGGLE_PERIOD_MS)
    {
        HAL_GPIO_TogglePin(LED_GPIO_Port, LED_Pin);
        lastToggleTick = now;
    }
}

/* ═══════════════════════════════════════════════════════════════════════════
 *  CheckButton  –  Debounced button poll, sends UART message on change
 *
 *  B1 on Nucleo is active LOW (pressed = GPIO_PIN_RESET).
 *  We report PRESSED on falling edge and RELEASED on rising edge.
 * ═══════════════════════════════════════════════════════════════════════════ */
static void CheckButton(void)
{
    GPIO_PinState currentState = HAL_GPIO_ReadPin(Button_GPIO_Port, Button_Pin);
    uint32_t now = HAL_GetTick();

    /* Only act after debounce window has elapsed since last state change */
    if (currentState != lastButtonState)
    {
        if ((now - lastDebounceTick) >= DEBOUNCE_MS)
        {
            lastButtonState  = currentState;
            lastDebounceTick = now;

            if (currentState == GPIO_PIN_RESET)   /* Falling edge → pressed  */
            {
                UART_SendString("\r\n[BTN] BUTTON PRESSED\r\n> ");
            }
            else                                   /* Rising edge  → released */
            {
                UART_SendString("\r\n[BTN] BUTTON RELEASED\r\n> ");
            }
        }
    }
    else
    {
        /* Reset debounce timer when state is stable */
        lastDebounceTick = now;
    }
}

/* ═══════════════════════════════════════════════════════════════════════════
 *  UART_SendString  –  Blocking transmit helper
 * ═══════════════════════════════════════════════════════════════════════════ */
static void UART_SendString(const char *str)
{
    HAL_UART_Transmit(&huart2, (uint8_t *)str, strlen(str), HAL_MAX_DELAY);
}

/* ─── String utilities ──────────────────────────────────────────────────── */

/* Remove leading and trailing spaces/tabs/CR/LF in-place */
static void TrimString(char *str)
{
    if (!str || *str == '\0') return;

    /* Trim trailing whitespace */
    int len = strlen(str);
    while (len > 0 && (str[len-1] == ' ' || str[len-1] == '\t' ||
                        str[len-1] == '\r' || str[len-1] == '\n'))
    {
        str[--len] = '\0';
    }

    /* Trim leading whitespace */
    char *start = str;
    while (*start == ' ' || *start == '\t') start++;

    if (start != str)
    {
        memmove(str, start, strlen(start) + 1);
    }
}

/* Convert string to upper case in-place */
static void ToUpperCase(char *str)
{
    while (*str)
    {
        if (*str >= 'a' && *str <= 'z') *str -= 32;
        str++;
    }
}
/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
