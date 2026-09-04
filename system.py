saldo = []
desc = []

def aumentar():
    aumentar = float(input('Digite o valor para acrescentar no saldo R$'))
    saldo.append(aumentar)
    print(f'Valor de R${aumentar:.2f} ADICIONADO. ')
def diminuir():
    diminuir = float(input('Digite o valor para diminuir no saldo R$'))
    saldo.append(-diminuir)
    print(f'Valor de R${diminuir:.2f} DIMINUIDO. ')

def descricao():
     descricao = str(input('Descrição para controle de gasto: '))
     desc.append(descricao)
def menu():
    while True:
            print('-' * 30)
            print(f"""MENU DE OPÇÕES:

1- ADICIONAR VALOR
2- DIMINUIR VALOR
3- EXTRATO DE VALORES

                  """)

            print('')
            opcao = int(input('Escolha a opção para atualizar o saldo: '))

#parei aqui
            if opcao == 1:
                descricao()
                aumentar()



            if opcao == 2:
                descricao()
                diminuir()

            if opcao == 3:
                print('-' * 30)
                print('EXTRATO DE VALORES DE ENTRADA E SAIDA')
                print('-' * 20)
                print('')
            for descri, valor in zip(desc, saldo):
                    print(f"- Descrição: {descri} / VALOR R${valor:.2f}")
            print(f'- Saldo atual: R$ {sum(saldo):.2f}')

menu()


