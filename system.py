saldo = []
desc = []

def aumentar():
    aumentar = float(input('- Digite o valor para acrescentar no saldo R$ '))
    while aumentar <= 0:
        print('<ERRO> - Digite um valor válido para aumentar do saldo.')
        aumentar = float(input('- Digite o valor para aumentar no saldo R$'))
    saldo.append(aumentar)
    print('')
    print(f'     Valor de R${aumentar:.2f} ADICIONADO.     ')

def diminuir():
    diminuir = float(input('- Digite o valor para diminuir no saldo R$'))
    while diminuir <= 0:
        print('<ERRO> - Digite um valor válido para diminuir do saldo.')
        diminuir = float(input('- Digite o valor para diminuir no saldo R$'))
    saldo.append(-diminuir)
    print('')
    print(f'     Valor de R${diminuir:.2f} DIMINUIDO.      ')
    
def descricao():
     descricao = str(input('- Descrição para controle de gasto: '))
     desc.append(descricao)

def menu():
    while True:
        try:
            print('-' * 30)
            print(f"""       MENU DE OPÇÕES:

    1- ADICIONAR VALOR
    2- DIMINUIR VALOR
    3- EXTRATO DE VALORES
    4- SAIR DO SISTEMA
                 """)
                    
            print('-' * 30)
            
            opcao = int(input('Escolha a opção para atualizar o saldo: '))


            if opcao == 1:
                    descricao()
                    aumentar()

            if opcao == 2:
                    descricao()
                    diminuir()

            if opcao == 3:
                    print('-' * 30)
                    print('HISTÓRICO DE VALORES DE ENTRADA E SAIDA')
                    print('')
                    for descri, valor in zip(desc, saldo):
                        print(f"- Descrição: {descri} / VALOR R${valor:.2f}")
                        print('-' * 30)
                    print(f'- Saldo atual: R$ {sum(saldo):.2f}')
            if opcao == 4:
                    print('Saindo do sistema...')
                    break


        except ValueError:
            print('<ERRO> - Digite apenas números nas opções.')
menu()


