void main() {
  for (int i = 1; i <= 9; i++) {
    String row = "";
    for (int j = 1; j <= i; j++) {
      String expression = "${j}x$i=${i * j}";
      row += expression.padRight(6); // 每个表达式占6个字符宽度
    }
    print(row);
  }
}