document.addEventListener('DOMContentLoaded', () => {
    // Campos que afetam o cálculo
    const valorContratoInput = document.getElementById('valor_contrato');
    const custoProdutoInput = document.getElementById('custo_produto');
    const percComissaoInput = document.getElementById('percentual_comissao');
    const resultadoSpan = document.getElementById('resultado_liquido');

    const campos = [valorContratoInput, custoProdutoInput, percComissaoInput];

    campos.forEach(campo => {
        campo.addEventListener('input', calcularLiquido);
    });

    function calcularLiquido() {
        const valorContrato = parseFloat(valorContratoInput.value) || 0;
        const custoProduto = parseFloat(custoProdutoInput.value) || 0;
        const percComissao = parseFloat(percComissaoInput.value) / 100 || 0;

        if (valorContrato === 0) {
            resultadoSpan.textContent = "R$ 0,00";
            return;
        }

        // Nova fórmula
        const valorComissao = valorContrato * percComissao;
        const liquidoFinal = valorContrato - valorComissao - custoProduto;

        resultadoSpan.textContent = liquidoFinal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    }
});